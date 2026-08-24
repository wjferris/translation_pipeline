"""Tests for decoupled translation and bounded Spanish playback."""

from __future__ import annotations

from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch

from live_audio_translation.demo import DemoPipeline, DemoState, SpeechJob, SpeechJobQueue


def job(text: str) -> SpeechJob:
    return SpeechJob(text, {"id": text, "text": text}, time.monotonic_ns())


class SpeechJobQueueTests(unittest.TestCase):
    def test_fifo_order_and_full_queue_evicts_only_unstarted_oldest_job(self) -> None:
        queue = SpeechJobQueue(2)
        active, _, _ = queue.enqueue(job("active"))
        self.assertIsNone(active)
        playing, _, _ = queue.take()
        self.assertEqual(playing.text, "active")
        queue.enqueue(job("stale"))
        queue.enqueue(job("middle"))
        evicted, _, _ = queue.enqueue(job("newest"))
        self.assertEqual(evicted.text, "stale")
        first, _, _ = queue.take()
        second, _, _ = queue.take()
        self.assertEqual([first.text, second.text], ["middle", "newest"])

    def test_close_with_discard_returns_unstarted_jobs(self) -> None:
        queue = SpeechJobQueue(2)
        queue.enqueue(job("one"))
        queue.enqueue(job("two"))
        self.assertEqual([item.text for item in queue.close(discard=True)], ["one", "two"])
        item, depth, age = queue.take()
        self.assertIsNone(item)
        self.assertEqual(depth, 0)
        self.assertIsNone(age)


class DemoPipelinePlaybackTests(unittest.TestCase):
    def make_pipeline(self, capacity: int = 2) -> tuple[DemoPipeline, DemoState]:
        args = SimpleNamespace(playback_queue_size=capacity, output_device=None, translation_model="local")
        state = DemoState()
        return DemoPipeline(args, state, object(), None), state

    def test_translation_publishes_spanish_before_audio_is_played(self) -> None:
        pipeline, state = self.make_pipeline()
        event = {"id": "phrase-1", "text": "Hello.", "source_ids": ["segment-1"]}
        with patch("live_audio_translation.demo.translate", return_value="Hola."):
            pipeline._translate_event(object(), event)
        self.assertIn("Hola.", [item["text"] for item in state.events_after(0)])
        queued, _ = pipeline.speech_queue.snapshot()
        self.assertEqual(queued, 1)
        pipeline.speech_queue.close(discard=True)

    def test_playback_worker_uses_one_at_a_time_fifo_order(self) -> None:
        pipeline, _ = self.make_pipeline()
        pipeline.speech_queue.enqueue(job("uno"))
        pipeline.speech_queue.enqueue(job("dos"))
        pipeline.speech_queue.close(discard=False)
        spoken: list[str] = []
        with patch("live_audio_translation.demo.play_text", side_effect=lambda _voice, text, _device, **_kwargs: spoken.append(text)):
            pipeline._playback_speech()
        self.assertEqual(spoken, ["uno", "dos"])

    def test_playback_failure_does_not_block_later_admitted_job(self) -> None:
        pipeline, _ = self.make_pipeline()
        pipeline.speech_queue.enqueue(job("fails"))
        pipeline.speech_queue.enqueue(job("continues"))
        pipeline.speech_queue.close(discard=False)
        spoken: list[str] = []

        def speak(_voice: object, text: str, _device: object, **_kwargs: object) -> None:
            if text == "fails":
                raise RuntimeError("device unavailable")
            spoken.append(text)

        with patch("live_audio_translation.demo.play_text", side_effect=speak):
            pipeline._playback_speech()
        self.assertEqual(spoken, ["continues"])

    def test_overload_keeps_browser_text_and_newest_unstarted_audio(self) -> None:
        pipeline, state = self.make_pipeline(capacity=1)
        with patch("live_audio_translation.demo.translate", side_effect=["uno", "dos", "tres"]):
            for number in range(3):
                pipeline._translate_event(object(), {"id": f"phrase-{number}", "text": "English"})
        spanish = [item["text"] for item in state.events_after(0) if item["kind"] == "spanish"]
        self.assertEqual(spanish, ["uno", "dos", "tres"])
        next_job, _, _ = pipeline.speech_queue.take()
        self.assertEqual(next_job.text, "tres")
        pipeline.speech_queue.close(discard=True)
