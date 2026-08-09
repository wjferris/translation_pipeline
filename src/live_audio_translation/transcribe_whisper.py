"""Transcribe one local audio file using the installed Whisper CLI."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path


DEFAULT_MODEL_PATH = Path("/opt/local/share/whisper/models/medium.bin")
DEFAULT_AUDIO_PATH = (
    Path(__file__).resolve().parents[1] / "resources" / "voxtral-winning-call.mp3"
)


class TranscriptionCancelled(Exception):
    """Raised when an active local Whisper process is cancelled."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe a local audio file with the installed Whisper CLI."
    )
    parser.add_argument(
        "audio",
        nargs="?",
        type=Path,
        default=DEFAULT_AUDIO_PATH,
        help="Path to an English audio file (default: bundled 25-second sample).",
    )
    parser.add_argument("--language", default="en", help="Spoken language code (default: en).")
    return parser.parse_args()


def transcribe(
    audio_path: Path,
    language: str,
    *,
    show_status: bool = True,
    cancel_event: threading.Event | None = None,
) -> str:
    """Run Whisper and return its text-file transcript."""
    whisper_command = shutil.which("whisper")
    if whisper_command is None:
        raise RuntimeError("Whisper executable not found on PATH.")

    model_path = Path(os.environ.get("WHISPER_MODEL_PATH", DEFAULT_MODEL_PATH))
    if not model_path.is_file():
        raise RuntimeError(f"Whisper model file not found: {model_path}")

    if show_status:
        print(f"Transcribing with local Whisper model: {model_path.name}", file=sys.stderr)
    with tempfile.TemporaryDirectory(prefix="whisper-transcript-") as temp_dir:
        output_prefix = Path(temp_dir) / "transcript"
        process = subprocess.Popen(
            [
                whisper_command,
                "--model",
                str(model_path),
                "--language",
                language,
                "--output-txt",
                "--output-file",
                str(output_prefix),
                "--no-timestamps",
                "--no-prints",
                str(audio_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            env={
                **os.environ,
                "DYLD_FALLBACK_LIBRARY_PATH": ":".join(
                    filter(
                        None,
                        [os.environ.get("DYLD_FALLBACK_LIBRARY_PATH"), "/opt/local/lib"],
                    )
                ),
            },
        )
        while True:
            try:
                stdout, stderr = process.communicate(timeout=0.1)
                break
            except subprocess.TimeoutExpired:
                if cancel_event is not None and cancel_event.is_set():
                    process.terminate()
                    try:
                        process.communicate(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                    raise TranscriptionCancelled

        if process.returncode != 0:
            detail = (stderr or stdout).strip()
            raise RuntimeError(detail or "Whisper exited without an error message.")

        transcript_path = output_prefix.with_suffix(".txt")
        if not transcript_path.is_file():
            raise RuntimeError("Whisper completed but did not create a transcript file.")
        return transcript_path.read_text(encoding="utf-8").strip()


def main() -> None:
    args = parse_args()
    if not args.audio.is_file():
        print(f"Audio file not found or unreadable: {args.audio}", file=sys.stderr)
        raise SystemExit(2)

    try:
        print(transcribe(args.audio, args.language))
    except Exception as exc:
        print(f"Transcription failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
