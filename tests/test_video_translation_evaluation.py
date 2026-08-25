"""Tests for the paired-video translation evaluation scaffold."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "evaluate_video_translation.py"
RECORDED_MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "evaluate_recorded_vad.py"
RECORDED_SPEC = importlib.util.spec_from_file_location("evaluate_recorded_vad", RECORDED_MODULE_PATH)
assert RECORDED_SPEC and RECORDED_SPEC.loader
recorded_evaluation = importlib.util.module_from_spec(RECORDED_SPEC)
sys.modules[RECORDED_SPEC.name] = recorded_evaluation
RECORDED_SPEC.loader.exec_module(recorded_evaluation)
SPEC = importlib.util.spec_from_file_location("evaluate_video_translation", MODULE_PATH)
assert SPEC and SPEC.loader
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


class VideoTranslationEvaluationTests(unittest.TestCase):
    def test_translation_report_includes_model_and_similarity(self) -> None:
        cues = [evaluation.SubtitleCue(0, 2_000, "Hola mundo.")]
        events = [evaluation.EvaluationEvent("segment-1", "Hola mundo", 0, 2_000)]
        report = evaluation.translation_report(cues, events, "webrtc", "translategemma:4b")
        self.assertIn("Video translation evaluation: webrtc", report)
        self.assertIn("Translation model: `translategemma:4b`", report)
        self.assertIn("Whole-document normalized text similarity: 100.0%", report)

    def test_extract_audio_builds_mono_16khz_ffmpeg_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "english.mp4"
            wav = Path(directory) / "english.wav"
            video.touch()
            with patch.object(evaluation, "run_ffmpeg") as run:
                evaluation.extract_audio(video, wav)
            command = run.call_args.args[0]
        self.assertIn("-map", command)
        self.assertIn("0:a:0", command)
        self.assertIn("-ac", command)
        self.assertIn("1", command)
        self.assertIn("-ar", command)
        self.assertIn("16000", command)


if __name__ == "__main__":
    unittest.main()
