"""Tests for bounded local ASR and translation phrase context."""

from __future__ import annotations

import io
import queue
import threading
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import numpy as np

from live_audio_translation import transcribe_microphone, transcribe_whisper, translate_stream
from live_audio_translation.phrase_context import EnglishContext, TranslationContext


class PhraseContextTests(unittest.TestCase):
    def test_english_context_uses_recent_finalized_phrases_and_excludes_cues(self) -> None:
        context = EnglishContext(2, maximum_chars=100)
        self.assertIsNone(context.prompt())
        context.add("First complete phrase.")
        context.add("[BLANK_AUDIO]")
        context.add("Second complete phrase.")
        self.assertEqual(context.prompt(), "First complete phrase. Second complete phrase.")

    def test_english_context_zero_disables_and_long_text_is_bounded(self) -> None:
        context = EnglishContext(0, maximum_chars=10)
        context.add("This text is never retained.")
        self.assertIsNone(context.prompt())
        bounded = EnglishContext(1, maximum_chars=12)
        bounded.add("one two three four")
        self.assertEqual(bounded.prompt(), "three four")

    def test_translation_context_keeps_order_and_caps_recent_pairs(self) -> None:
        context = TranslationContext(2, maximum_chars=100)
        context.add("one", "uno")
        context.add("two", "dos")
        context.add("three", "tres")
        self.assertEqual([(pair.english, pair.spanish) for pair in context.pairs()], [("two", "dos"), ("three", "tres")])

    def test_translation_messages_keep_context_separate_from_current_phrase(self) -> None:
        context = TranslationContext(2)
        context.add("Previous English.", "Español anterior.")
        messages = translate_stream.translation_messages("Current English.", context)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Previous English.", messages[1]["content"])
        self.assertEqual(messages[2], {"role": "assistant", "content": "Español anterior."})
        self.assertEqual(messages[-1]["content"], "Current English phrase:\nCurrent English.")
        self.assertEqual(
            translate_stream.translation_messages("Current English.", TranslationContext(0)),
            [{"role": "user", "content": translate_stream.PROMPT + "Current English."}],
        )

    def test_whisper_command_adds_prompt_only_when_context_is_available(self) -> None:
        command = transcribe_whisper.transcription_command(
            "whisper", transcribe_whisper.DEFAULT_MODEL_PATH, "en", transcribe_whisper.DEFAULT_MODEL_PATH,
            transcribe_whisper.DEFAULT_MODEL_PATH, prompt="Previous phrase."
        )
        self.assertEqual(command[-2:], ["--prompt", "Previous phrase."])
        no_prompt = transcribe_whisper.transcription_command(
            "whisper", transcribe_whisper.DEFAULT_MODEL_PATH, "en", transcribe_whisper.DEFAULT_MODEL_PATH,
            transcribe_whisper.DEFAULT_MODEL_PATH,
        )
        self.assertNotIn("--prompt", no_prompt)

    def test_microphone_worker_passes_only_prior_emitted_text_to_whisper(self) -> None:
        windows: queue.Queue[transcribe_microphone.AudioWindow] = queue.Queue()
        windows.put(transcribe_microphone.AudioWindow(np.zeros((160, 1), dtype=np.float32), 0, 10))
        windows.put(transcribe_microphone.AudioWindow(np.zeros((160, 1), dtype=np.float32), 10, 20))
        stop = threading.Event()
        original_get = windows.get

        def get(timeout: float) -> transcribe_microphone.AudioWindow:
            try:
                return original_get(block=False)
            except queue.Empty:
                stop.set()
                raise

        prompts: list[str | None] = []
        with patch.object(windows, "get", side_effect=get), patch(
            "live_audio_translation.transcribe_microphone.transcribe",
            side_effect=lambda *_args, prompt=None, **_kwargs: prompts.append(prompt) or (
                "First." if len(prompts) == 1 else "First. Second."
            ),
        ), redirect_stdout(io.StringIO()):
            transcribe_microphone.transcribe_windows(
                windows, queue.Queue(), stop, "en", "text", whisper_context_phrases=1
            )
        self.assertEqual(prompts, [None, "First."])


class TranslationStreamContextTests(unittest.TestCase):
    def test_successful_pair_becomes_context_for_the_next_phrase(self) -> None:
        class Client:
            def __init__(self) -> None:
                self.messages: list[list[dict[str, str]]] = []

            def chat(self, **kwargs: object):
                self.messages.append(kwargs["messages"])
                text = "Uno." if len(self.messages) == 1 else "Dos."
                return type("Response", (), {"message": type("Message", (), {"content": text})()})()

        client = Client()
        output = io.StringIO()
        translate_stream.run(
            client, "model", input_stream=io.StringIO('{"id":"1","text":"One."}\n{"id":"2","text":"Two."}\n'),
            output_stream=output, error_stream=io.StringIO(), context_phrases=2,
        )
        self.assertEqual(len(client.messages[0]), 1)
        self.assertEqual([message["role"] for message in client.messages[1]], ["system", "user", "assistant", "user"])
        self.assertIn("One.", client.messages[1][1]["content"])
        self.assertIn('"text": "Uno."', output.getvalue())
        self.assertIn('"text": "Dos."', output.getvalue())

    def test_failed_translation_does_not_become_later_context(self) -> None:
        class Client:
            def __init__(self) -> None:
                self.calls = 0
                self.messages: list[list[dict[str, str]]] = []

            def chat(self, **kwargs: object):
                self.calls += 1
                self.messages.append(kwargs["messages"])
                if self.calls == 1:
                    raise RuntimeError("unavailable")
                return type("Response", (), {"message": type("Message", (), {"content": "Dos."})()})()

        client = Client()
        translate_stream.run(
            client, "model", input_stream=io.StringIO('{"id":"1","text":"One."}\n{"id":"2","text":"Two."}\n'),
            output_stream=io.StringIO(), error_stream=io.StringIO(), context_phrases=2,
        )
        self.assertEqual(len(client.messages[1]), 1)


if __name__ == "__main__":
    unittest.main()
