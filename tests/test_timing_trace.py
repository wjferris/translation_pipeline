"""Tests for local, asynchronous live-pipeline timing traces."""

from __future__ import annotations

import json
import queue
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from live_audio_translation import buffer_phrases
from live_audio_translation import demo
from live_audio_translation.speak_stream import play_text
from live_audio_translation.timing_trace import (
    TraceRun,
    empty_timestamps,
    latency_slope_ms_per_second,
    milliseconds,
)
from live_audio_translation.transcribe_microphone import CaptureClock, audio_window


def traced_event(
    event_id: str,
    timestamps: dict[str, int | None],
    *,
    segment_id: str | None = None,
    phrase_id: str | None = None,
    source_segment_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "id": event_id,
        "text": "example text",
        "start_ms": 0,
        "end_ms": 1_000,
        "timing": {
            "segment_id": segment_id,
            "phrase_id": phrase_id,
            "source_segment_ids": source_segment_ids or [],
            "timestamps_ns": timestamps,
            "queue_depths": {"asr": {"enqueue": 0, "dequeue": 0}},
        },
    }


class TimingTraceTests(unittest.TestCase):
    def test_demo_timing_trace_is_default_on_with_explicit_baseline_switch(self) -> None:
        with patch("sys.argv", ["demo"]):
            self.assertFalse(demo.parse_args().no_timing_trace)
        with patch("sys.argv", ["demo", "--no-timing-trace"]):
            self.assertTrue(demo.parse_args().no_timing_trace)

    def test_allocates_private_incrementing_run_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "runs"
            first = TraceRun.create({}, root=root)
            second = TraceRun.create({}, root=root)
            try:
                self.assertEqual(first.run_id[-3:], "001")
                self.assertEqual(second.run_id[-3:], "002")
                self.assertEqual(stat.S_IMODE(first.directory.stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE((first.directory / "manifest.json").stat().st_mode), 0o600)
            finally:
                first.close("completed")
                second.close("completed")

    def test_trace_writes_correlated_stage_records_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace = TraceRun.create({}, root=Path(directory), timebase_ns=1)
            timestamps = empty_timestamps()
            timestamps.update(
                {
                    "source_audio_start": 0,
                    "source_audio_end": 1_000_000_000,
                    "vad_detected_start": 100_000_000,
                    "vad_segment_closed": 1_000_000_000,
                    "asr_start": 1_100_000_000,
                    "asr_complete": 1_600_000_000,
                }
            )
            trace.stage("asr", traced_event("segment-1", timestamps, segment_id="segment-1"))
            trace.stage(
                "phrases",
                traced_event(
                    "phrase-1",
                    {"phrase_buffer_received": 1_700_000_000, "phrase_buffer_released": 1_800_000_000},
                    phrase_id="phrase-1",
                    source_segment_ids=["segment-1"],
                ),
            )
            trace.stage(
                "translations",
                traced_event(
                    "phrase-1",
                    {"translation_start": 1_900_000_000, "translation_complete": 2_100_000_000},
                    phrase_id="phrase-1",
                    source_segment_ids=["segment-1"],
                ),
            )
            trace.stage(
                "playback",
                traced_event(
                    "phrase-1",
                    {
                        "tts_start": 2_200_000_000,
                        "tts_first_audio": 2_250_000_000,
                        "tts_complete": 2_500_000_000,
                        "playback_start": 2_300_000_000,
                        "playback_complete": 3_300_000_000,
                    },
                    phrase_id="phrase-1",
                    source_segment_ids=["segment-1"],
                ),
            )
            trace.close("completed")

            metric = json.loads((trace.directory / "segments.ndjson").read_text().strip())
            self.assertEqual(metric["completion_state"], "completed")
            self.assertEqual(metric["segment_id"], "segment-1")
            self.assertEqual(metric["derived_metrics"]["asr_processing_duration_ms"], 500.0)
            self.assertEqual(metric["derived_metrics"]["asr_rtf"], 0.5)
            self.assertEqual(metric["derived_metrics"]["end_to_end_playback_start_ms"], 1300.0)
            self.assertEqual(metric["queue_depths"]["asr"]["enqueue"], 0)
            self.assertTrue((trace.directory / "timing.ndjson").is_file())

    def test_overflow_marks_trace_incomplete_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace = TraceRun.create({}, root=Path(directory), queue_size=1)
            with patch.object(trace._queue, "put_nowait", side_effect=queue.Full):
                trace.stage("asr", {"id": "segment-1", "text": "ignored"})
            trace.close("completed")
            manifest = json.loads((trace.directory / "manifest.json").read_text())
            self.assertFalse(manifest["trace_complete"])
            self.assertGreaterEqual(manifest["trace_overflow_count"], 1)

    def test_trace_marks_a_translated_but_skipped_audio_segment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace = TraceRun.create({}, root=Path(directory), timebase_ns=1)
            timestamps = empty_timestamps()
            timestamps.update({"source_audio_start": 0, "source_audio_end": 1_000_000_000, "translation_complete": 2_000_000_000})
            trace.stage("asr", traced_event("segment-1", timestamps, segment_id="segment-1"))
            trace.stage("phrases", traced_event("phrase-1", {}, phrase_id="phrase-1", source_segment_ids=["segment-1"]))
            trace.stage("translations", traced_event("phrase-1", timestamps, phrase_id="phrase-1", source_segment_ids=["segment-1"]))
            skipped = traced_event("phrase-1", {"audio_skipped": 3_000_000_000}, phrase_id="phrase-1", source_segment_ids=["segment-1"])
            skipped["timing"]["audio_state"] = "skipped"
            skipped["timing"]["audio_skip_reason"] = "playback_queue_full"
            skipped["timing"]["queue_depths"] = {"speech_playback": {"logical_pending": 3, "oldest_queued_age_ms": 6000}}
            trace.stage("speech_queue", skipped)
            trace.close("completed")
            metric = json.loads((trace.directory / "segments.ndjson").read_text().strip())
            self.assertEqual(metric["completion_state"], "audio_skipped")
            self.assertEqual(metric["audio_skip_reason"], "playback_queue_full")
            self.assertEqual(metric["derived_metrics"]["audio_skipped_latency_ms"], 2000.0)

    def test_milliseconds_returns_none_for_unavailable_boundary(self) -> None:
        self.assertIsNone(milliseconds(None, 1))
        self.assertEqual(milliseconds(1_000_000, 3_500_000), 2.5)

    def test_latency_slope_distinguishes_stable_jitter_and_backlog_fixtures(self) -> None:
        def records(latencies: list[float]) -> list[dict[str, object]]:
            return [
                {
                    "source_end_ms": index * 10_000,
                    "derived_metrics": {"end_to_end_playback_start_ms": latency},
                }
                for index, latency in enumerate(latencies)
            ]

        self.assertAlmostEqual(latency_slope_ms_per_second(records([5000, 5000, 5000])), 0.0)
        self.assertAlmostEqual(latency_slope_ms_per_second(records([5000, 5100, 4900])), -5.0)
        self.assertAlmostEqual(latency_slope_ms_per_second(records([1000, 2000, 3000])), 100.0)

    def test_source_window_has_segment_and_vad_timestamps(self) -> None:
        window = audio_window(
            np.zeros((160, 1), dtype=np.float32),
            160,
            320,
            segment_id="segment-1",
            clock=CaptureClock(timebase_ns=1_000, started_ns=1_000),
            vad_detected_sample=200,
            vad_closed_sample=320,
        )
        self.assertEqual(window.timing["segment_id"], "segment-1")
        self.assertEqual(window.timing["timestamps_ns"]["source_audio_start"], 10_000_000)
        self.assertEqual(window.timing["timestamps_ns"]["vad_detected_start"], 12_500_000)

    def test_phrase_buffer_preserves_source_segment_lineage(self) -> None:
        buffer = buffer_phrases.PhraseBuffer(timebase_ns=1)
        source = {
            "id": "segment-1",
            "text": "Hello.",
            "start_ms": 0,
            "end_ms": 100,
            "timing": {"segment_id": "segment-1"},
        }
        with patch(
            "live_audio_translation.buffer_phrases.relative_monotonic_ns",
            side_effect=[100, 200],
        ):
            events = buffer.add(source, now=1.0)
        self.assertEqual(events[0]["timing"]["source_segment_ids"], ["segment-1"])
        self.assertEqual(events[0]["timing"]["timestamps_ns"]["phrase_buffer_released"], 200)

    def test_piper_timing_callback_marks_generation_and_playback_boundaries(self) -> None:
        class Chunk:
            audio_float_array = np.array([0.1, -0.1], dtype=np.float32)
            sample_rate = 22_050
            sample_channels = 1

        class Voice:
            def synthesize(self, _text: str):
                yield Chunk()

        class Output:
            def start(self) -> None:
                pass

            def write(self, _audio: np.ndarray) -> None:
                pass

            def stop(self) -> None:
                pass

            def close(self) -> None:
                pass

        boundaries: list[str] = []
        with patch("live_audio_translation.speak_stream.sd.OutputStream", return_value=Output()):
            play_text(Voice(), "Hola", None, on_timing=boundaries.append)
        self.assertEqual(
            boundaries,
            ["tts_start", "tts_first_audio", "playback_start", "tts_complete", "playback_complete"],
        )
