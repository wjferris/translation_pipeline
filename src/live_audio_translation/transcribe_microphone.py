"""Continuously capture microphone audio into overlapping Whisper windows."""

from __future__ import annotations

import argparse
import json
import queue
import re
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from live_audio_translation.transcribe_whisper import (
    TranscriptionCancelled,
    transcribe,
)


SAMPLE_RATE = 16_000
BLOCK_SECONDS = 0.1
WINDOW_QUEUE_SIZE = 3


@dataclass
class AudioWindow:
    """Audio plus its approximate position in the captured microphone stream."""

    audio: np.ndarray
    start_ms: int
    end_ms: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Continuously transcribe overlapping microphone windows with local Whisper."
    )
    parser.add_argument(
        "--window-seconds",
        "--chunk-seconds",
        dest="window_seconds",
        type=float,
        default=5.0,
        help="Whisper window duration in seconds (default: 5).",
    )
    parser.add_argument(
        "--stride-seconds",
        type=float,
        default=4.0,
        help="Seconds between the starts of adjacent windows (default: 4).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Stop after this many seconds; useful for a short test.",
    )
    parser.add_argument("--language", default="en", help="Spoken language code (default: en).")
    parser.add_argument(
        "--output-format",
        choices=("text", "ndjson"),
        default="text",
        help="Output completed transcripts as readable text or newline-delimited JSON (default: text).",
    )
    return parser.parse_args()


def normalize_word(word: str) -> str:
    return re.sub(r"[^\w']", "", word).lower()


def remove_overlap(previous: str, current: str) -> str:
    """Remove a conservative multiword suffix/prefix overlap from current."""
    previous_words = previous.split()
    current_words = current.split()
    limit = min(len(previous_words), len(current_words), 20)
    for count in range(limit, 1, -1):
        prior = [normalize_word(word) for word in previous_words[-count:]]
        upcoming = [normalize_word(word) for word in current_words[:count]]
        if prior == upcoming and all(prior):
            return " ".join(current_words[count:])
    return current


class WindowSegmenter:
    """Turn continuous callback blocks into overlapping fixed-size windows."""

    def __init__(
        self,
        blocks: queue.Queue[np.ndarray],
        windows: queue.Queue[AudioWindow],
        warnings: queue.Queue[str],
        stop_event: threading.Event,
        window_seconds: float,
        stride_seconds: float,
    ) -> None:
        self.blocks = blocks
        self.windows = windows
        self.warnings = warnings
        self.stop_event = stop_event
        self.window_samples = round(window_seconds * SAMPLE_RATE)
        self.stride_samples = round(stride_seconds * SAMPLE_RATE)

    def put_window(self, window: AudioWindow) -> None:
        try:
            self.windows.put_nowait(window)
        except queue.Full:
            try:
                self.windows.get_nowait()
            except queue.Empty:
                pass
            self.windows.put_nowait(window)
            self.warnings.put(
                "Whisper is behind live capture; discarded an older transcription window."
            )

    def run(self) -> None:
        buffer = np.empty((0, 1), dtype=np.float32)
        buffer_start = 0
        received = 0
        next_window_start = 0
        while not self.stop_event.is_set():
            try:
                block = self.blocks.get(timeout=0.1)
            except queue.Empty:
                continue
            buffer = np.concatenate((buffer, block))
            received += len(block)
            while received >= next_window_start + self.window_samples:
                offset = next_window_start - buffer_start
                self.put_window(
                    AudioWindow(
                        audio=buffer[offset : offset + self.window_samples].copy(),
                        start_ms=round(next_window_start * 1000 / SAMPLE_RATE),
                        end_ms=round(
                            (next_window_start + self.window_samples) * 1000 / SAMPLE_RATE
                        ),
                    )
                )
                next_window_start += self.stride_samples

            discard = next_window_start - buffer_start
            if discard > 0:
                buffer = buffer[discard:]
                buffer_start = next_window_start


def capture_callback(
    blocks: queue.Queue[np.ndarray],
    warnings: queue.Queue[str],
) -> callable:
    def callback(indata: np.ndarray, _frames: int, _time: object, status: sd.CallbackFlags) -> None:
        if status:
            warnings.put(f"Microphone status: {status}")
        try:
            blocks.put_nowait(indata.copy())
        except queue.Full:
            warnings.put("Microphone capture is overloaded; discarded an audio block.")

    return callback


def transcribe_windows(
    windows: queue.Queue[AudioWindow],
    warnings: queue.Queue[str],
    stop_event: threading.Event,
    language: str,
    output_format: str,
) -> None:
    previous = ""
    sequence = 0
    while not stop_event.is_set():
        try:
            window = windows.get(timeout=0.1)
        except queue.Empty:
            continue
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            window_path = Path(temp_file.name)
        try:
            sf.write(window_path, window.audio, SAMPLE_RATE)
            transcript = transcribe(
                window_path,
                language,
                show_status=False,
                cancel_event=stop_event,
            )
            if transcript:
                new_text = remove_overlap(previous, transcript)
                if new_text:
                    sequence += 1
                    if output_format == "ndjson":
                        event = {
                            "id": f"segment-{sequence}",
                            "text": new_text,
                            "start_ms": window.start_ms,
                            "end_ms": window.end_ms,
                        }
                        print(json.dumps(event, ensure_ascii=False), flush=True)
                        print(new_text, file=sys.stderr, flush=True)
                    else:
                        print(new_text, flush=True)
                previous = transcript
        except TranscriptionCancelled:
            break
        except Exception as exc:
            warnings.put(f"Whisper window failed: {exc}")
        finally:
            window_path.unlink(missing_ok=True)


def validate_args(args: argparse.Namespace) -> None:
    if args.window_seconds <= 0:
        raise ValueError("--window-seconds must be greater than zero.")
    if args.stride_seconds <= 0:
        raise ValueError("--stride-seconds must be greater than zero.")
    if args.stride_seconds > args.window_seconds:
        raise ValueError("--stride-seconds cannot exceed --window-seconds.")
    if args.duration is not None and args.duration <= 0:
        raise ValueError("--duration must be greater than zero.")


def main() -> None:
    args = parse_args()
    try:
        validate_args(args)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc

    blocks: queue.Queue[np.ndarray] = queue.Queue(maxsize=100)
    windows: queue.Queue[AudioWindow] = queue.Queue(maxsize=WINDOW_QUEUE_SIZE)
    warnings: queue.Queue[str] = queue.Queue()
    stop_event = threading.Event()
    segmenter = WindowSegmenter(
        blocks, windows, warnings, stop_event, args.window_seconds, args.stride_seconds
    )
    segmenter_thread = threading.Thread(target=segmenter.run, name="audio-segmenter")
    worker_thread = threading.Thread(
        target=transcribe_windows,
        args=(windows, warnings, stop_event, args.language, args.output_format),
        name="whisper-worker",
    )
    segmenter_thread.start()
    worker_thread.start()

    started_at = time.monotonic()
    print(
        "Listening continuously to the default microphone "
        f"with {args.window_seconds:g}-second windows every {args.stride_seconds:g} seconds. "
        "Press Ctrl-C to stop.",
        file=sys.stderr,
    )
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=round(BLOCK_SECONDS * SAMPLE_RATE),
            callback=capture_callback(blocks, warnings),
        ):
            while args.duration is None or time.monotonic() - started_at < args.duration:
                try:
                    while True:
                        print(warnings.get_nowait(), file=sys.stderr)
                except queue.Empty:
                    pass
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping microphone transcription...", file=sys.stderr)
    except sd.PortAudioError as exc:
        print(
            "Microphone capture failed. Grant microphone access to the terminal or IDE "
            "running this command, then try again.\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    finally:
        stop_event.set()
        segmenter_thread.join(timeout=2)
        worker_thread.join(timeout=3)
        print("Microphone transcription stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
