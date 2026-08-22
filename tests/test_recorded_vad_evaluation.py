"""Tests for the developer-only recorded VAD evaluation scaffold."""

from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

from live_audio_translation.transcribe_microphone import AudioWindow, VADSegmenter
from live_audio_translation.transcribe_whisper import TranscriptSegment, TranscriptToken


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "evaluate_recorded_vad.py"
SPEC = importlib.util.spec_from_file_location("evaluate_recorded_vad", MODULE_PATH)
assert SPEC and SPEC.loader
evaluation = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = evaluation
SPEC.loader.exec_module(evaluation)


class RecordedVadEvaluationTests(unittest.TestCase):
    def write_wav(self, directory: str, *, sample_rate: int = 16_000, channels: int = 1) -> Path:
        path = Path(directory) / "input.wav"
        samples = np.zeros((sample_rate, channels), dtype=np.float32)
        sf.write(path, samples, sample_rate)
        return path

    def test_read_wav_requires_16khz_mono_wav(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            valid = self.write_wav(directory)
            self.assertEqual(evaluation.read_wav(valid).shape, (16_000, 1))
            invalid = self.write_wav(directory, sample_rate=8_000)
            with self.assertRaisesRegex(ValueError, "16 kHz mono WAV"):
                evaluation.read_wav(invalid)

    def test_source_range_preserves_absolute_timestamp_origin(self) -> None:
        audio = np.zeros((32_000, 1), dtype=np.float32)
        selected, start = evaluation.select_source_range(audio, 0.5, 1.5)
        self.assertEqual(start, 8_000)
        self.assertEqual(selected.shape, (16_000, 1))

    def test_parse_srt_and_report_include_timeline_and_approximate_label(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            srt = Path(directory) / "reference.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello world.\n")
            cues = evaluation.parse_srt(srt)
            report = evaluation.comparison_report(
                cues, [evaluation.EvaluationEvent("segment-1", "Hello world", 0, 2000)], "webrtc"
            )
        self.assertEqual(cues[0].start_ms, 0)
        self.assertIn("approximate normalized-text comparison", report)
        self.assertIn("Reference: Hello world.", report)
        self.assertIn("Recognized: Hello world", report)

    def test_prepare_output_rejects_existing_artifacts_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "artifacts"
            output.mkdir()
            (output / "transcript.ndjson").touch()
            with self.assertRaisesRegex(ValueError, "already contains artifacts"):
                evaluation.prepare_output(output, overwrite=False)
            evaluation.prepare_output(output, overwrite=True)

    def test_webrtc_replay_emits_source_timestamped_phrase(self) -> None:
        args = argparse.Namespace(
            vad_aggressiveness=2, vad_silence_seconds=0.06, vad_pre_roll_seconds=0.03,
            vad_min_phrase_seconds=0.03, vad_max_phrase_seconds=1.0,
        )
        audio = np.zeros((16_000, 1), dtype=np.float32)
        speech = [True, True, False, False] + [False] * 29
        with patch.object(VADSegmenter, "is_speech", side_effect=speech):
            windows = evaluation.replay_webrtc_windows(audio, 16_000, args)
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].start_ms, 1000)
        events = evaluation.evaluate_webrtc(windows, "en", transcribe_fn=lambda *_args, **_kwargs: "Hello")
        self.assertEqual(events[0].start_ms, 1000)
        self.assertEqual(events[0].text, "Hello")

    def test_silero_evaluation_transcribes_each_phrase_once(self) -> None:
        windows = [
            AudioWindow(np.zeros((80_000, 1), dtype=np.float32), 0, 5000),
            AudioWindow(np.zeros((80_000, 1), dtype=np.float32), 4000, 9000),
        ]
        with patch.object(evaluation, "evaluate_webrtc", return_value=[evaluation.EvaluationEvent("segment-1", "first", 0, 4000)]) as evaluate:
            events = evaluation.evaluate_silero(windows, "en")
        evaluate.assert_called_once()
        self.assertEqual([(event.text, event.start_ms, event.end_ms) for event in events], [
            ("first", 0, 4000),
        ])
