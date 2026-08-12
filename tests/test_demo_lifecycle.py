"""Tests for background demo-session lifecycle control."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from live_audio_translation import demo_service
from live_audio_translation.stop_demo import stop


class StopDemoTests(unittest.TestCase):
    def test_detached_service_restores_sigint_handling(self) -> None:
        with patch("live_audio_translation.demo_service.os.fork", return_value=0), patch(
            "live_audio_translation.demo_service.os.setsid"
        ) as set_session, patch("live_audio_translation.demo_service.signal.signal") as set_signal:
            demo_service._detach_session()
        set_session.assert_called_once_with()
        set_signal.assert_called_once_with(
            demo_service.signal.SIGINT, demo_service.signal.default_int_handler
        )

    def test_stop_interrupts_the_isolated_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "demo.pid"
            pid_file.write_text("1234\n", encoding="ascii")
            with patch("live_audio_translation.stop_demo._is_session_leader", return_value=True), patch(
                "live_audio_translation.stop_demo.os.killpg"
            ) as kill_group, patch(
                "live_audio_translation.stop_demo._is_running", side_effect=[True, False, False]
            ):
                self.assertEqual(stop(pid_file), 0)
            kill_group.assert_called_once()
            self.assertFalse(pid_file.exists())

    def test_stop_removes_a_stale_pid_file_without_signalling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "demo.pid"
            pid_file.write_text("1234\n", encoding="ascii")
            with patch("live_audio_translation.stop_demo._is_session_leader", return_value=False), patch(
                "live_audio_translation.stop_demo.os.killpg"
            ) as kill_group:
                self.assertEqual(stop(pid_file), 0)
            kill_group.assert_not_called()
            self.assertFalse(pid_file.exists())
