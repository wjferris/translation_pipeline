"""Capture local microphone audio and send final speech segments to Whisper.

The default mode uses fixed overlapping windows. The opt-in VAD mode keeps
capture continuous but segments on natural pauses before invoking Whisper.
Completed English text is printed for people or emitted as NDJSON for the
translation pipeline.
"""

from __future__ import annotations

import argparse
import json
import queue
import re
import sys
import tempfile
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad

from live_audio_translation.transcribe_whisper import (
    TranscriptionCancelled,
    transcribe,
)


SAMPLE_RATE = 16_000
BLOCK_SECONDS = 0.1
WINDOW_QUEUE_SIZE = 3
VAD_FRAME_SECONDS = 0.03


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
        "--segmentation",
        choices=("fixed", "vad"),
        default="fixed",
        help="Audio segmentation method (default: fixed).",
    )
    parser.add_argument(
        "--vad-aggressiveness",
        type=int,
        default=2,
        help="WebRTC VAD aggressiveness from 0 to 3 (default: 2).",
    )
    parser.add_argument(
        "--vad-silence-seconds",
        type=float,
        default=0.7,
        help="Silence that ends a VAD phrase (default: 0.7).",
    )
    parser.add_argument(
        "--vad-pre-roll-seconds",
        type=float,
        default=0.3,
        help="Audio retained before VAD detects speech (default: 0.3).",
    )
    parser.add_argument(
        "--vad-min-phrase-seconds",
        type=float,
        default=0.7,
        help="Shortest VAD phrase sent to Whisper (default: 0.7).",
    )
    parser.add_argument(
        "--vad-max-phrase-seconds",
        type=float,
        default=10.0,
        help="Maximum VAD phrase duration before a forced split (default: 10).",
    )
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
    """Turn continuous callback blocks into overlapping fixed-size audio windows."""

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


class VADSegmenter:
    """Turn continuous capture blocks into pause-delimited speech phrases."""

    def __init__(
        self,
        blocks: queue.Queue[np.ndarray],
        windows: queue.Queue[AudioWindow],
        warnings: queue.Queue[str],
        stop_event: threading.Event,
        aggressiveness: int,
        silence_seconds: float,
        pre_roll_seconds: float,
        min_phrase_seconds: float,
        max_phrase_seconds: float,
    ) -> None:
        self.blocks = blocks
        self.windows = windows
        self.warnings = warnings
        self.stop_event = stop_event
        self.vad = webrtcvad.Vad(aggressiveness)
        self.frame_samples = round(VAD_FRAME_SECONDS * SAMPLE_RATE)
        self.silence_frames = max(1, round(silence_seconds / VAD_FRAME_SECONDS))
        self.pre_roll_frames = max(1, round(pre_roll_seconds / VAD_FRAME_SECONDS))
        self.min_phrase_samples = round(min_phrase_seconds * SAMPLE_RATE)
        self.max_phrase_samples = round(max_phrase_seconds * SAMPLE_RATE)
        self.pending = np.empty(0, dtype=np.float32)
        self.received = 0
        self.pre_roll: deque[np.ndarray] = deque(maxlen=self.pre_roll_frames)
        self.phrase_frames: list[np.ndarray] = []
        self.phrase_start_sample = 0
        self.trailing_silence = 0

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
                "Whisper is behind live capture; discarded an older transcription phrase."
            )

    def is_speech(self, frame: np.ndarray) -> bool:
        pcm = np.clip(frame, -1.0, 1.0)
        return self.vad.is_speech((pcm * 32767).astype(np.int16).tobytes(), SAMPLE_RATE)

    def finish_phrase(self, end_sample: int) -> None:
        if not self.phrase_frames:
            return
        audio = np.concatenate(self.phrase_frames).reshape(-1, 1)
        if len(audio) >= self.min_phrase_samples:
            self.put_window(
                AudioWindow(
                    audio=audio,
                    start_ms=round(self.phrase_start_sample * 1000 / SAMPLE_RATE),
                    end_ms=round(end_sample * 1000 / SAMPLE_RATE),
                )
            )
        self.phrase_frames = []
        self.trailing_silence = 0

    def process_frame(self, frame: np.ndarray, frame_start: int) -> None:
        speech = self.is_speech(frame)
        if not self.phrase_frames:
            self.pre_roll.append(frame)
            if not speech:
                return
            self.phrase_frames = list(self.pre_roll)
            self.phrase_start_sample = frame_start - (len(self.pre_roll) - 1) * self.frame_samples
            self.trailing_silence = 0
            return

        self.phrase_frames.append(frame)
        self.trailing_silence = 0 if speech else self.trailing_silence + 1
        phrase_samples = sum(len(part) for part in self.phrase_frames)
        if phrase_samples >= self.max_phrase_samples or self.trailing_silence >= self.silence_frames:
            self.finish_phrase(frame_start + self.frame_samples)
            self.pre_roll.clear()

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                block = self.blocks.get(timeout=0.1)
            except queue.Empty:
                continue
            self.pending = np.concatenate((self.pending, block[:, 0]))
            while len(self.pending) >= self.frame_samples:
                frame = self.pending[: self.frame_samples].copy()
                self.pending = self.pending[self.frame_samples :]
                frame_start = self.received
                self.received += self.frame_samples
                self.process_frame(frame, frame_start)
        if self.phrase_frames:
            self.finish_phrase(self.received)


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
    """Write queued audio to temporary WAV files and emit finalized transcripts."""
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
    """Reject invalid fixed-window and VAD command-line combinations early."""
    if args.window_seconds <= 0:
        raise ValueError("--window-seconds must be greater than zero.")
    if args.stride_seconds <= 0:
        raise ValueError("--stride-seconds must be greater than zero.")
    if args.stride_seconds > args.window_seconds:
        raise ValueError("--stride-seconds cannot exceed --window-seconds.")
    if args.duration is not None and args.duration <= 0:
        raise ValueError("--duration must be greater than zero.")
    if not 0 <= args.vad_aggressiveness <= 3:
        raise ValueError("--vad-aggressiveness must be between 0 and 3.")
    for option in (
        "vad_silence_seconds",
        "vad_pre_roll_seconds",
        "vad_min_phrase_seconds",
        "vad_max_phrase_seconds",
    ):
        if getattr(args, option) <= 0:
            raise ValueError(f"--{option.replace('_', '-')} must be greater than zero.")
    if args.vad_min_phrase_seconds > args.vad_max_phrase_seconds:
        raise ValueError("--vad-min-phrase-seconds cannot exceed --vad-max-phrase-seconds.")


def main() -> None:
    """Run microphone capture, segmentation, and local Whisper transcription."""
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
    if args.segmentation == "vad":
        segmenter = VADSegmenter(
            blocks,
            windows,
            warnings,
            stop_event,
            args.vad_aggressiveness,
            args.vad_silence_seconds,
            args.vad_pre_roll_seconds,
            args.vad_min_phrase_seconds,
            args.vad_max_phrase_seconds,
        )
        listening_message = (
            "Listening continuously to the default microphone with local VAD "
            f"phrases ending after {args.vad_silence_seconds:g} seconds of silence "
            f"or {args.vad_max_phrase_seconds:g} seconds maximum. Press Ctrl-C to stop."
        )
    else:
        segmenter = WindowSegmenter(
            blocks, windows, warnings, stop_event, args.window_seconds, args.stride_seconds
        )
        listening_message = (
            "Listening continuously to the default microphone "
            f"with {args.window_seconds:g}-second windows every {args.stride_seconds:g} seconds. "
            "Press Ctrl-C to stop."
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
    print(listening_message, file=sys.stderr)
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
