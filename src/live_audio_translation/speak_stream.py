"""Speak translated Spanish NDJSON events with a local Piper voice.

The worker keeps one Piper model loaded, reads translated event objects from
standard input, and plays each phrase in order through the selected local audio
output device. It has no network, Zoom, or virtual-audio-device behavior.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, TextIO

import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice


DEFAULT_MODEL_PATH = Path("models/piper/es_MX-claude-high.onnx")
BRACKETED_CUE = re.compile(r"\[[^\[\]]*\]")


def parse_args() -> argparse.Namespace:
    """Parse local Piper model and output-device selection."""
    parser = argparse.ArgumentParser(
        description="Speak Spanish NDJSON events with a local Piper voice."
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=f"Local Piper .onnx voice model (default: {DEFAULT_MODEL_PATH}).",
    )
    parser.add_argument(
        "--output-device",
        help="Sounddevice output device name or index (default: system output device).",
    )
    return parser.parse_args()


def validate_event(value: Any) -> dict[str, Any]:
    """Ensure an incoming stream event has Spanish text to speak."""
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    if not isinstance(value.get("text"), str) or not value["text"].strip():
        raise ValueError("input event requires a non-empty string 'text' field")
    return value


def spoken_text(text: str) -> str:
    """Remove complete bracketed non-speech cues before Piper synthesis."""
    return " ".join(BRACKETED_CUE.sub(" ", text).split())


def play_text(
    voice: PiperVoice,
    text: str,
    output_device: str | None,
    on_timing: Callable[[str], None] | None = None,
) -> None:
    """Synthesize one phrase and write Piper's PCM chunks to an audio device."""
    text = spoken_text(text)
    if not text:
        return
    stream: sd.OutputStream | None = None
    if on_timing is not None:
        on_timing("tts_start")
    try:
        for chunk in voice.synthesize(text):
            if stream is None and on_timing is not None:
                on_timing("tts_first_audio")
            audio = np.asarray(chunk.audio_float_array, dtype=np.float32)
            if audio.ndim == 1:
                audio = audio.reshape(-1, 1)
            if stream is None:
                stream = sd.OutputStream(
                    samplerate=chunk.sample_rate,
                    channels=chunk.sample_channels,
                    dtype="float32",
                    device=output_device,
                )
                stream.start()
                if on_timing is not None:
                    on_timing("playback_start")
            stream.write(audio)
        if on_timing is not None:
            on_timing("tts_complete")
    finally:
        if stream is not None:
            stream.stop()
            stream.close()
            if on_timing is not None:
                on_timing("playback_complete")


def run(
    voice: PiperVoice,
    output_device: str | None,
    *,
    input_stream: TextIO = sys.stdin,
    error_stream: TextIO = sys.stderr,
) -> None:
    """Read and speak Spanish NDJSON events until standard input closes."""
    for line_number, raw_line in enumerate(input_stream, start=1):
        if not raw_line.strip():
            continue
        try:
            event = validate_event(json.loads(raw_line))
        except (json.JSONDecodeError, ValueError) as error:
            print(f"Skipping input line {line_number}: {error}", file=error_stream)
            continue
        try:
            play_text(voice, event["text"], output_device)
        except Exception as error:
            event_id = event.get("id", f"line {line_number}")
            print(f"Could not speak {event_id}: {error}", file=error_stream)


def main() -> None:
    """Load the selected local Piper voice and start speaker playback."""
    args = parse_args()
    if not args.model.is_file():
        print(
            f"Piper voice model not found: {args.model}\n"
            "Download a local Piper voice with: "
            "uv run python -m piper.download_voices --download-dir models/piper "
            "es_MX-claude-high",
            file=sys.stderr,
        )
        raise SystemExit(2)
    try:
        voice = PiperVoice.load(args.model)
        run(voice, args.output_device)
    except KeyboardInterrupt:
        print("Piper speech worker stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
