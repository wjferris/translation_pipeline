"""Gracefully stop the isolated local BabelFish demo session."""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

from live_audio_translation.demo_service import PID_FILE_ENV


def _pid_file() -> Path:
    value = os.environ.get(PID_FILE_ENV)
    if not value:
        raise RuntimeError(f"{PID_FILE_ENV} is required to stop the demo service.")
    return Path(value)


def _read_pid(pid_file: Path) -> int | None:
    try:
        value = pid_file.read_text(encoding="ascii").strip()
        return int(value)
    except (OSError, ValueError):
        return None


def _is_session_leader(pid: int) -> bool:
    try:
        return os.getsid(pid) == pid and os.getpgid(pid) == pid
    except ProcessLookupError:
        return False


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def stop(pid_file: Path, timeout_seconds: float = 30) -> int:
    """Interrupt the recorded demo process group and wait for its cleanup."""
    pid = _read_pid(pid_file)
    if pid is None:
        print("BabelFish demo is not running.", file=sys.stderr)
        return 0
    if not _is_session_leader(pid):
        pid_file.unlink(missing_ok=True)
        print("Removed stale BabelFish demo PID file.", file=sys.stderr)
        return 0

    os.killpg(pid, signal.SIGINT)
    deadline = time.monotonic() + timeout_seconds
    while _is_running(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    if _is_running(pid):
        print("BabelFish is still stopping; active audio may be finishing.", file=sys.stderr)
        return 1
    pid_file.unlink(missing_ok=True)
    print("BabelFish demo stopped.", file=sys.stderr)
    return 0


def main() -> None:
    try:
        raise SystemExit(stop(_pid_file()))
    except RuntimeError as error:
        print(f"Cannot stop BabelFish demo: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
