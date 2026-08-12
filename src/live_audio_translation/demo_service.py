"""Run the local demo in a detached, launcher-owned POSIX session."""

from __future__ import annotations

import atexit
import os
import signal
from pathlib import Path

PID_FILE_ENV = "BABELFISH_DEMO_PID_FILE"


def _pid_file() -> Path:
    value = os.environ.get(PID_FILE_ENV)
    if not value:
        raise RuntimeError(f"{PID_FILE_ENV} is required to launch the demo service.")
    return Path(value)


def _detach_session() -> None:
    """Fork once, become a session leader, and restore graceful interrupts."""
    if os.name != "posix":
        raise RuntimeError("Background demo sessions require a POSIX operating system.")
    if os.fork():
        raise SystemExit(0)
    os.setsid()
    # Shells commonly make an asynchronous job ignore SIGINT. Restore Python's
    # normal handler so scripts/stop-demo can trigger demo.py's cleanup path.
    signal.signal(signal.SIGINT, signal.default_int_handler)


def _write_pid_file(pid_file: Path) -> None:
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(f"{os.getpid()}\n", encoding="ascii")
    pid_file.chmod(0o600)


def _remove_own_pid_file(pid_file: Path) -> None:
    try:
        if pid_file.read_text(encoding="ascii").strip() == str(os.getpid()):
            pid_file.unlink(missing_ok=True)
    except OSError:
        pass


def run_demo() -> None:
    """Import native demo dependencies only after the child has detached."""
    from live_audio_translation import demo

    demo.main()


def main() -> None:
    """Detach, publish the stable session-leader PID, then run the demo."""
    pid_file = _pid_file()
    _detach_session()
    _write_pid_file(pid_file)
    atexit.register(_remove_own_pid_file, pid_file)
    run_demo()


if __name__ == "__main__":
    main()
