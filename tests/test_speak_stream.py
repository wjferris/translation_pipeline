"""Regression tests for Piper-specific speech sanitization."""

from __future__ import annotations

import unittest

from live_audio_translation.speak_stream import play_text, spoken_text


class PiperCueSuppressionTests(unittest.TestCase):
    def test_removes_cues_and_normalizes_surrounding_whitespace(self) -> None:
        self.assertEqual(spoken_text("Hola [blank audio] mundo"), "Hola mundo")
        self.assertEqual(spoken_text("[music] Hola [applause] mundo [noise]"), "Hola mundo")

    def test_preserves_unmatched_brackets(self) -> None:
        self.assertEqual(spoken_text("Hola [sin cerrar"), "Hola [sin cerrar")
        self.assertEqual(spoken_text("Hola sin abrir]"), "Hola sin abrir]")

    def test_play_text_passes_only_spoken_text_to_piper(self) -> None:
        class Voice:
            def __init__(self) -> None:
                self.texts: list[str] = []

            def synthesize(self, text: str):
                self.texts.append(text)
                return iter(())

        voice = Voice()
        play_text(voice, "Hola [blank audio] mundo", None)
        self.assertEqual(voice.texts, ["Hola mundo"])

    def test_cue_only_text_skips_piper_and_timing_callbacks(self) -> None:
        class Voice:
            def synthesize(self, _text: str):
                raise AssertionError("cue-only text must not reach Piper")

        callbacks: list[str] = []
        play_text(Voice(), " [blank audio] [music] ", None, on_timing=callbacks.append)
        self.assertEqual(callbacks, [])
