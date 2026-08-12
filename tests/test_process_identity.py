"""Tests for opt-in demo process identity behavior."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from live_audio_translation.process_identity import PROCESS_TITLE_ENV, set_demo_process_title


class ProcessIdentityTests(unittest.TestCase):
    def test_no_title_is_set_without_demo_environment(self) -> None:
        with patch.dict("os.environ", {}, clear=True), patch(
            "live_audio_translation.process_identity.setproctitle"
        ) as set_title:
            self.assertIsNone(set_demo_process_title())
        set_title.assert_not_called()

    def test_requested_title_is_applied(self) -> None:
        with patch.dict("os.environ", {PROCESS_TITLE_ENV: "BabelFish ASR"}, clear=True), patch(
            "live_audio_translation.process_identity.setproctitle"
        ) as set_title:
            self.assertEqual(set_demo_process_title(), "BabelFish ASR")
        set_title.assert_called_once_with("BabelFish ASR")
