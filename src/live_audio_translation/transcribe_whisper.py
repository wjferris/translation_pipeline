"""Run the locally installed Whisper CLI against one English audio file.

This module is the shared local-ASR adapter used by both the file experiment
and continuous microphone process. It honors ``WHISPER_MODEL_PATH`` and can
terminate a running Whisper child process when live capture is stopped.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL_PATH = Path("/opt/local/share/whisper/models/medium.bin")
DEFAULT_SILERO_VAD_MODEL_NAME = "ggml-silero-v6.2.0.bin"
DEFAULT_AUDIO_PATH = (
    Path(__file__).resolve().parents[1] / "resources" / "voxtral-winning-call.mp3"
)


class TranscriptionCancelled(Exception):
    """Raised when an active local Whisper process is cancelled."""


@dataclass(frozen=True)
class TranscriptToken:
    """One timed Whisper token, relative to its input audio file."""

    text: str
    start_ms: int
    end_ms: int


@dataclass(frozen=True)
class TranscriptSegment:
    """One Whisper result segment, timed relative to its input audio file."""

    text: str
    start_ms: int
    end_ms: int
    tokens: tuple[TranscriptToken, ...] = ()


def default_whisper_model() -> Path:
    """Prefer a source-built whisper.cpp medium model when it is available."""
    command = shutil.which("whisper")
    if command is not None:
        executable = Path(command).resolve()
        try:
            candidate = executable.parents[2] / "models" / "ggml-medium.bin"
        except IndexError:
            candidate = DEFAULT_MODEL_PATH
        if candidate.is_file():
            return candidate
    return DEFAULT_MODEL_PATH


def whisper_command() -> str:
    """Return the configured local Whisper CLI or raise an actionable error."""
    command = shutil.which("whisper")
    if command is None:
        raise RuntimeError("Whisper executable not found on PATH.")
    return command


def default_silero_vad_model(whisper_executable: str) -> Path:
    """Locate the upstream Silero asset beside a source-built whisper-cli."""
    executable = Path(whisper_executable).resolve()
    try:
        source_root = executable.parents[2]
    except IndexError:
        return Path(DEFAULT_SILERO_VAD_MODEL_NAME)
    return source_root / "models" / DEFAULT_SILERO_VAD_MODEL_NAME


def validate_silero_vad(
    model_path: Path | None = None,
    *,
    executable: str | None = None,
) -> Path:
    """Confirm that the local Whisper CLI can run its integrated Silero VAD."""
    try:
        executable = executable or whisper_command()
    except RuntimeError as error:
        raise ValueError(f"{error} Use --vad-backend webrtc.") from error
    selected_model = model_path or Path(
        os.environ.get("SILERO_VAD_MODEL_PATH", default_silero_vad_model(executable))
    )
    if not selected_model.is_file():
        raise ValueError(
            "Silero VAD model not found: "
            f"{selected_model}. Set --silero-vad-model or SILERO_VAD_MODEL_PATH, "
            "or use --vad-backend webrtc."
        )
    try:
        result = subprocess.run(
            [executable, "--help"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(
            f"Cannot inspect Whisper for integrated Silero VAD support: {error}. "
            "Use --vad-backend webrtc."
        ) from error
    help_text = f"{result.stdout}\n{result.stderr}"
    missing = [
        option for option in ("--vad", "--vad-model", "--output-json-full") if option not in help_text
    ]
    if result.returncode != 0 or missing:
        detail = ", ".join(missing) or "a usable --help response"
        raise ValueError(
            f"Installed Whisper does not support integrated Silero VAD ({detail} missing). "
            "Use a recent whisper.cpp build or --vad-backend webrtc."
        )
    return selected_model


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


def transcription_command(
    executable: str,
    model_path: Path,
    language: str,
    output_prefix: Path,
    audio_path: Path,
    silero_vad_model: Path | None = None,
    output_json: bool = False,
    output_json_full: bool = False,
    no_gpu: bool = False,
    prompt: str | None = None,
) -> list[str]:
    """Build a compatible local Whisper CLI request for one audio file."""
    command = [
        executable,
        "--model",
        str(model_path),
        "--language",
        language,
        "--output-json-full" if output_json_full else "--output-json" if output_json else "--output-txt",
        "--output-file",
        str(output_prefix),
        "--no-prints",
        str(audio_path),
    ]
    if silero_vad_model is not None:
        command.extend(["--vad", "--vad-model", str(silero_vad_model)])
    if no_gpu:
        command.append("--no-gpu")
    if prompt:
        command.extend(["--prompt", prompt])
    return command


def read_transcript_segments(output_prefix: Path) -> list[TranscriptSegment]:
    """Read timestamped segments from whisper.cpp's JSON output."""
    transcript_path = output_prefix.with_suffix(".json")
    if not transcript_path.is_file():
        raise RuntimeError("Whisper completed but did not create a JSON transcript.")
    try:
        payload = json.loads(transcript_path.read_text(encoding="utf-8"))
        raw_segments = payload["transcription"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError(f"Whisper produced invalid JSON transcript output: {error}") from error
    segments: list[TranscriptSegment] = []
    for raw_segment in raw_segments:
        compressed_tokens: list[TranscriptToken] = []
        try:
            text = str(raw_segment["text"]).strip()
            offsets = raw_segment["offsets"]
            start_ms = int(offsets["from"])
            end_ms = int(offsets["to"])
            for raw_token in raw_segment.get("tokens", []):
                token_text = str(raw_token["text"])
                token_offsets = raw_token["offsets"]
                token_start_ms = int(token_offsets["from"])
                token_end_ms = int(token_offsets["to"])
                if token_text and not token_text.startswith("[_") and token_end_ms > token_start_ms:
                    compressed_tokens.append(TranscriptToken(token_text, token_start_ms, token_end_ms))
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError(f"Whisper JSON segment is missing timing offsets: {error}") from error
        if text and end_ms > start_ms:
            tokens = remap_vad_token_offsets(compressed_tokens, start_ms, end_ms)
            segments.append(TranscriptSegment(text, start_ms, end_ms, tokens))
    return segments


def remap_vad_token_offsets(
    tokens: list[TranscriptToken], segment_start_ms: int, segment_end_ms: int
) -> tuple[TranscriptToken, ...]:
    """Map whisper.cpp's VAD-compressed token time onto original segment time."""
    if not tokens:
        return ()
    compressed_start = tokens[0].start_ms
    compressed_end = tokens[-1].end_ms
    compressed_duration = compressed_end - compressed_start
    if compressed_duration <= 0:
        return ()
    scale = (segment_end_ms - segment_start_ms) / compressed_duration
    return tuple(
        TranscriptToken(
            token.text,
            segment_start_ms + round((token.start_ms - compressed_start) * scale),
            segment_start_ms + round((token.end_ms - compressed_start) * scale),
        )
        for token in tokens
    )


def run_whisper(command: list[str], cancel_event: threading.Event | None) -> None:
    """Run one Whisper command, allowing live capture to cancel it cleanly."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        env={
            **os.environ,
            "DYLD_FALLBACK_LIBRARY_PATH": ":".join(
                filter(None, [os.environ.get("DYLD_FALLBACK_LIBRARY_PATH"), "/opt/local/lib"])
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


def transcribe(
    audio_path: Path,
    language: str,
    *,
    show_status: bool = True,
    cancel_event: threading.Event | None = None,
    silero_vad_model: Path | None = None,
    no_gpu: bool = False,
    prompt: str | None = None,
) -> str:
    """Run Whisper locally and return its plain-text transcript.

    Status stays on standard error. ``cancel_event`` lets the microphone worker
    interrupt the child process cleanly during shutdown.
    """
    executable = whisper_command()

    model_path = Path(os.environ.get("WHISPER_MODEL_PATH", default_whisper_model()))
    if not model_path.is_file():
        raise RuntimeError(f"Whisper model file not found: {model_path}")

    if show_status:
        print(f"Transcribing with local Whisper model: {model_path.name}", file=sys.stderr)
    with tempfile.TemporaryDirectory(prefix="whisper-transcript-") as temp_dir:
        output_prefix = Path(temp_dir) / "transcript"
        command = transcription_command(
            executable, model_path, language, output_prefix, audio_path, silero_vad_model,
            no_gpu=no_gpu, prompt=prompt,
        )
        run_whisper(command, cancel_event)

        transcript_path = output_prefix.with_suffix(".txt")
        if not transcript_path.is_file():
            raise RuntimeError("Whisper completed but did not create a transcript file.")
        return transcript_path.read_text(encoding="utf-8").strip()


def transcribe_timed(
    audio_path: Path,
    language: str,
    *,
    cancel_event: threading.Event | None = None,
    silero_vad_model: Path,
    no_gpu: bool = False,
    prompt: str | None = None,
) -> list[TranscriptSegment]:
    """Run integrated Silero VAD and return Whisper's timestamped segments."""
    executable = whisper_command()
    model_path = Path(os.environ.get("WHISPER_MODEL_PATH", default_whisper_model()))
    if not model_path.is_file():
        raise RuntimeError(f"Whisper model file not found: {model_path}")
    with tempfile.TemporaryDirectory(prefix="whisper-transcript-") as temp_dir:
        output_prefix = Path(temp_dir) / "transcript"
        command = transcription_command(
            executable,
            model_path,
            language,
            output_prefix,
            audio_path,
            silero_vad_model,
            output_json_full=True,
            no_gpu=no_gpu,
            prompt=prompt,
        )
        run_whisper(command, cancel_event)
        return read_transcript_segments(output_prefix)


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
