"""Tests for selecting the local microphone VAD backend."""

from __future__ import annotations

import queue
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from live_audio_translation import demo, transcribe_microphone, transcribe_whisper


class SileroCapabilityTests(unittest.TestCase):
    def test_accepts_whisper_with_integrated_vad_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "ggml-silero-v6.2.0.bin"
            model.touch()
            with patch(
                "live_audio_translation.transcribe_whisper.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    ["whisper", "--help"], 0, stdout="--vad --vad-model --output-json-full", stderr=""
                ),
            ):
                self.assertEqual(
                    transcribe_whisper.validate_silero_vad(model, executable="whisper"), model
                )

    def test_rejects_whisper_without_integrated_vad_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "ggml-silero-v6.2.0.bin"
            model.touch()
            with patch(
                "live_audio_translation.transcribe_whisper.subprocess.run",
                return_value=subprocess.CompletedProcess(["whisper", "--help"], 0, stdout="", stderr=""),
            ):
                with self.assertRaisesRegex(ValueError, "does not support integrated Silero"):
                    transcribe_whisper.validate_silero_vad(model, executable="whisper")

    def test_transcription_command_adds_silero_flags_only_when_selected(self) -> None:
        command = transcribe_whisper.transcription_command(
            "whisper", Path("medium.bin"), "en", Path("output"), Path("input.wav"), Path("silero.bin")
        )
        self.assertEqual(command[-3:], ["--vad", "--vad-model", "silero.bin"])
        baseline = transcribe_whisper.transcription_command(
            "whisper", Path("medium.bin"), "en", Path("output"), Path("input.wav")
        )
        self.assertNotIn("--vad", baseline)

    def test_reads_and_remaps_timestamped_whisper_segments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result"
            output.with_suffix(".json").write_text(
                '{"transcription":[{"text":" Hello","offsets":{"from":320,"to":1200},'
                '"tokens":[{"text":" Hello","offsets":{"from":100,"to":500}}]}]}'
            )
            self.assertEqual(
                transcribe_whisper.read_transcript_segments(output),
                [transcribe_whisper.TranscriptSegment(
                    "Hello", 320, 1200, (transcribe_whisper.TranscriptToken(" Hello", 320, 1200),)
                )],
            )


class VadBackendSelectionTests(unittest.TestCase):
    def test_silero_trims_any_exact_sentence_boundary_word(self) -> None:
        self.assertEqual(
            transcribe_microphone.remove_overlap(
                "He stopped at the station.",
                "station. While he waited.",
                trim_single_sentence_word=True,
            ),
            "While he waited.",
        )

    def test_silero_drops_segments_fully_covered_by_the_prior_window(self) -> None:
        segments = [
            transcribe_whisper.TranscriptSegment(
                "duplicate", 0, 850, (transcribe_whisper.TranscriptToken(" duplicate", 0, 850),)
            ),
            transcribe_whisper.TranscriptSegment(
                "new speech", 1100, 2600,
                (
                    transcribe_whisper.TranscriptToken(" new", 1100, 1800),
                    transcribe_whisper.TranscriptToken(" speech", 1800, 2600),
                ),
            ),
        ]
        self.assertEqual(
            transcribe_microphone.new_timed_segments(segments, 4000, 5000),
            [transcribe_whisper.TranscriptSegment(
                "new speech", 5100, 6600,
                (
                    transcribe_whisper.TranscriptToken(" new", 5100, 5800),
                    transcribe_whisper.TranscriptToken(" speech", 5800, 6600),
                ),
            )],
        )

    def test_silero_keeps_the_new_words_from_a_boundary_spanning_segment(self) -> None:
        segment = transcribe_whisper.TranscriptSegment(
            "at the station", 400, 1800,
            (
                transcribe_whisper.TranscriptToken(" at", 400, 800),
                transcribe_whisper.TranscriptToken(" the", 800, 1150),
                transcribe_whisper.TranscriptToken(" station", 1150, 1800),
            ),
        )
        self.assertEqual(
            transcribe_microphone.new_timed_segments([segment], 4000, 5000),
            [transcribe_whisper.TranscriptSegment(
                "the station", 4800, 5800,
                (
                    transcribe_whisper.TranscriptToken(" the", 4800, 5150),
                    transcribe_whisper.TranscriptToken(" station", 5150, 5800),
                ),
            )],
        )

    def test_silero_requires_vad_segmentation(self) -> None:
        args = SimpleNamespace(
            window_seconds=5.0,
            stride_seconds=4.0,
            duration=None,
            segmentation="fixed",
            vad_backend="silero",
            vad_aggressiveness=2,
            vad_silence_seconds=0.7,
            vad_pre_roll_seconds=0.3,
            vad_min_phrase_seconds=0.7,
            vad_max_phrase_seconds=10.0,
            input_gain_db=0.0,
        )
        with self.assertRaisesRegex(ValueError, "only valid with --segmentation vad"):
            transcribe_microphone.validate_args(args)

    def test_demo_forwards_silero_backend_and_model(self) -> None:
        args = SimpleNamespace(
            segmentation="vad",
            vad_backend="silero",
            language="en",
            silero_threshold=0.5,
            silero_min_silence_seconds=0.3,
            silero_speech_pad_seconds=0.1,
            silero_max_phrase_seconds=10.0,
            vad_silence_seconds=0.45,
            vad_aggressiveness=2,
            vad_pre_roll_seconds=0.3,
            vad_min_phrase_seconds=0.7,
            vad_max_phrase_seconds=10.0,
            window_seconds=5.0,
            stride_seconds=4.0,
            input_gain_db=30.0,
        )
        command = demo.microphone_command(args)
        self.assertIn("--vad-backend", command)
        self.assertEqual(command[-2:], ["--input-gain-db", "30.0"])
        self.assertNotIn("--vad-aggressiveness", command)


class InputGainTests(unittest.TestCase):
    def captured_block(self, samples: np.ndarray, input_gain: float) -> np.ndarray:
        blocks: queue.Queue[np.ndarray] = queue.Queue()
        callback = transcribe_microphone.capture_callback(blocks, queue.Queue(), input_gain)
        callback(samples, len(samples), None, None)
        return blocks.get_nowait()

    def test_zero_gain_preserves_captured_samples(self) -> None:
        samples = np.array([[-0.25], [0.5]], dtype=np.float32)
        captured = self.captured_block(samples, 1.0)
        np.testing.assert_array_equal(captured, samples)
        self.assertIsNot(captured, samples)

    def test_positive_gain_amplifies_captured_samples(self) -> None:
        samples = np.array([[-0.05], [0.05]], dtype=np.float32)
        captured = self.captured_block(samples, 10.0)
        np.testing.assert_allclose(captured, [[-0.5], [0.5]])

    def test_attenuation_reduces_captured_samples(self) -> None:
        samples = np.array([[-1.0], [1.0]], dtype=np.float32)
        captured = self.captured_block(samples, 10 ** (-6 / 20))
        np.testing.assert_allclose(captured, [[-0.501187], [0.501187]], rtol=1e-5)

    def test_amplified_samples_are_clipped(self) -> None:
        samples = np.array([[-0.25], [0.25]], dtype=np.float32)
        captured = self.captured_block(samples, 10.0)
        np.testing.assert_array_equal(captured, [[-1.0], [1.0]])

    def test_input_gain_accepts_boundary_values(self) -> None:
        base_args = dict(
            window_seconds=5.0,
            stride_seconds=4.0,
            duration=None,
            segmentation="fixed",
            vad_backend="webrtc",
            vad_aggressiveness=2,
            vad_silence_seconds=0.7,
            vad_pre_roll_seconds=0.3,
            vad_min_phrase_seconds=0.7,
            vad_max_phrase_seconds=10.0,
        )
        for gain in (transcribe_microphone.MIN_INPUT_GAIN_DB, transcribe_microphone.MAX_INPUT_GAIN_DB):
            transcribe_microphone.validate_args(SimpleNamespace(**base_args, input_gain_db=gain))
        with patch("sys.argv", ["transcribe-microphone", "--input-gain-db", "48"]):
            self.assertEqual(transcribe_microphone.parse_args().input_gain_db, 48.0)

    def test_input_gain_rejects_out_of_range_values(self) -> None:
        base_args = dict(
            window_seconds=5.0,
            stride_seconds=4.0,
            duration=None,
            segmentation="fixed",
            vad_backend="webrtc",
            vad_aggressiveness=2,
            vad_silence_seconds=0.7,
            vad_pre_roll_seconds=0.3,
            vad_min_phrase_seconds=0.7,
            vad_max_phrase_seconds=10.0,
        )
        for gain in (-48.1, 48.1):
            with self.assertRaisesRegex(ValueError, "--input-gain-db must be between -48 and 48"):
                transcribe_microphone.validate_args(SimpleNamespace(**base_args, input_gain_db=gain))
