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
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad
from silero_vad import VADIterator, load_silero_vad

from live_audio_translation.process_identity import set_demo_process_title
from live_audio_translation.timing_trace import (
    empty_timestamps,
    relative_monotonic_ns,
    trace_timebase_from_environment,
)
from live_audio_translation.transcribe_whisper import (
    TranscriptSegment,
    TranscriptToken,
    TranscriptionCancelled,
    transcribe,
    transcribe_timed,
    validate_silero_vad,
)


SAMPLE_RATE = 16_000
BLOCK_SECONDS = 0.1
WINDOW_QUEUE_SIZE = 3
VAD_FRAME_SECONDS = 0.03
MIN_INPUT_GAIN_DB = -48.0
MAX_INPUT_GAIN_DB = 48.0


@dataclass
class AudioWindow:
    """Audio plus its approximate position in the captured microphone stream."""

    audio: np.ndarray
    start_ms: int
    end_ms: int
    timing: dict[str, object] = field(default_factory=dict)


@dataclass
class CaptureClock:
    """Shared capture origin used to express source boundaries on the demo timeline."""

    timebase_ns: int | None
    started_ns: int | None = None

    def at_sample(self, sample: int) -> int | None:
        if self.timebase_ns is None or self.started_ns is None:
            return None
        return max(0, self.started_ns + round(sample * 1_000_000_000 / SAMPLE_RATE) - self.timebase_ns)


def audio_window(
    audio: np.ndarray,
    start_sample: int,
    end_sample: int,
    *,
    segment_id: str,
    clock: CaptureClock,
    vad_detected_sample: int | None = None,
    vad_closed_sample: int | None = None,
) -> AudioWindow:
    """Create a source segment with optional session-relative trace metadata."""
    timing: dict[str, object] = {}
    if clock.timebase_ns is not None:
        timestamps = empty_timestamps()
        timestamps["source_audio_start"] = clock.at_sample(start_sample)
        timestamps["source_audio_end"] = clock.at_sample(end_sample)
        timestamps["vad_detected_start"] = clock.at_sample(vad_detected_sample) if vad_detected_sample is not None else None
        timestamps["vad_segment_closed"] = clock.at_sample(vad_closed_sample) if vad_closed_sample is not None else None
        timing = {
            "segment_id": segment_id,
            "timestamps_ns": timestamps,
            "queue_depths": {"asr": {"enqueue": None, "dequeue": None}},
        }
    return AudioWindow(
        audio=audio,
        start_ms=round(start_sample * 1000 / SAMPLE_RATE),
        end_ms=round(end_sample * 1000 / SAMPLE_RATE),
        timing=timing,
    )


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
        "--vad-backend",
        choices=("webrtc", "silero"),
        default="webrtc",
        help="Local VAD backend for --segmentation vad (default: webrtc).",
    )
    parser.add_argument("--silero-threshold", type=float, default=0.5, help="Stateful Silero speech confidence threshold (default: 0.5).")
    parser.add_argument("--silero-min-silence-seconds", type=float, default=0.3, help="Stateful Silero silence that ends speech (default: 0.3).")
    parser.add_argument("--silero-speech-pad-seconds", type=float, default=0.1, help="Stateful Silero recognition padding (default: 0.1).")
    parser.add_argument("--silero-max-phrase-seconds", type=float, default=10.0, help="Stateful Silero maximum phrase duration (default: 10).")
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
    parser.add_argument(
        "--input-gain-db",
        type=float,
        default=0.0,
        help="Local microphone gain in dB from -48 through +48 (default: 0).",
    )
    return parser.parse_args()


def normalize_word(word: str) -> str:
    return re.sub(r"[^\w']", "", word).lower()


def remove_overlap(previous: str, current: str, *, trim_single_sentence_word: bool = False) -> str:
    """Remove a conservative exact suffix/prefix overlap from current text."""
    previous_words = previous.split()
    current_words = current.split()
    limit = min(len(previous_words), len(current_words), 20)
    minimum = 1 if trim_single_sentence_word else 2
    for count in range(limit, minimum - 1, -1):
        prior = [normalize_word(word) for word in previous_words[-count:]]
        upcoming = [normalize_word(word) for word in current_words[:count]]
        sentence_boundary = count > 1 or previous_words[-1].endswith((".", "!", "?"))
        if prior == upcoming and all(prior) and sentence_boundary:
            return " ".join(current_words[count:])
    return current


def new_timed_segments(
    segments: list[TranscriptSegment], window_start_ms: int, covered_until_ms: int
) -> list[TranscriptSegment]:
    """Keep the timed words that extend past earlier capture windows."""
    retained: list[TranscriptSegment] = []
    for segment in segments:
        timed_tokens = tuple(
            TranscriptToken(
                token.text, window_start_ms + token.start_ms, window_start_ms + token.end_ms
            )
            for token in segment.tokens
            if window_start_ms + token.end_ms > covered_until_ms
        )
        if timed_tokens:
            retained.append(
                TranscriptSegment(
                    "".join(token.text for token in timed_tokens).strip(),
                    timed_tokens[0].start_ms,
                    timed_tokens[-1].end_ms,
                    timed_tokens,
                )
            )
        elif not segment.tokens and window_start_ms + segment.end_ms > covered_until_ms:
            retained.append(
                TranscriptSegment(
                    segment.text, window_start_ms + segment.start_ms, window_start_ms + segment.end_ms
                )
            )
    return retained


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
        clock: CaptureClock | None = None,
    ) -> None:
        self.blocks = blocks
        self.windows = windows
        self.warnings = warnings
        self.stop_event = stop_event
        self.window_samples = round(window_seconds * SAMPLE_RATE)
        self.stride_samples = round(stride_seconds * SAMPLE_RATE)
        self.clock = clock or CaptureClock(None)
        self.sequence = 0

    def put_window(self, window: AudioWindow) -> None:
        trace = window.timing.get("queue_depths") if window.timing else None
        if isinstance(trace, dict):
            asr_queue = trace.get("asr")
            if isinstance(asr_queue, dict):
                asr_queue["enqueue"] = self.windows.qsize()
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
        while not self.stop_event.is_set() or not self.blocks.empty():
            try:
                block = self.blocks.get(timeout=0.1)
            except queue.Empty:
                continue
            buffer = np.concatenate((buffer, block))
            received += len(block)
            while received >= next_window_start + self.window_samples:
                offset = next_window_start - buffer_start
                self.sequence += 1
                self.put_window(
                    audio_window(
                        buffer[offset : offset + self.window_samples].copy(),
                        next_window_start,
                        next_window_start + self.window_samples,
                        segment_id=f"segment-{self.sequence}",
                        clock=self.clock,
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
        clock: CaptureClock | None = None,
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
        self.vad_detected_sample: int | None = None
        self.trailing_silence = 0
        self.clock = clock or CaptureClock(None)
        self.sequence = 0

    def put_window(self, window: AudioWindow) -> None:
        trace = window.timing.get("queue_depths") if window.timing else None
        if isinstance(trace, dict):
            asr_queue = trace.get("asr")
            if isinstance(asr_queue, dict):
                asr_queue["enqueue"] = self.windows.qsize()
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
            self.sequence += 1
            self.put_window(
                audio_window(
                    audio,
                    self.phrase_start_sample,
                    end_sample,
                    segment_id=f"segment-{self.sequence}",
                    clock=self.clock,
                    vad_detected_sample=self.vad_detected_sample,
                    vad_closed_sample=end_sample,
                )
            )
        self.phrase_frames = []
        self.trailing_silence = 0
        self.vad_detected_sample = None

    def process_frame(self, frame: np.ndarray, frame_start: int) -> None:
        speech = self.is_speech(frame)
        if not self.phrase_frames:
            self.pre_roll.append(frame)
            if not speech:
                return
            self.phrase_frames = list(self.pre_roll)
            self.phrase_start_sample = frame_start - (len(self.pre_roll) - 1) * self.frame_samples
            self.vad_detected_sample = frame_start
            self.trailing_silence = 0
            return

        self.phrase_frames.append(frame)
        self.trailing_silence = 0 if speech else self.trailing_silence + 1
        phrase_samples = sum(len(part) for part in self.phrase_frames)
        if phrase_samples >= self.max_phrase_samples or self.trailing_silence >= self.silence_frames:
            self.finish_phrase(frame_start + self.frame_samples)
            self.pre_roll.clear()

    def run(self) -> None:
        while not self.stop_event.is_set() or not self.blocks.empty():
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


class SileroSegmenter(VADSegmenter):
    """Continuous local Silero VAD that emits each phrase once."""

    def __init__(self, blocks: queue.Queue[np.ndarray], windows: queue.Queue[AudioWindow], warnings: queue.Queue[str], stop_event: threading.Event, threshold: float, silence_seconds: float, pad_seconds: float, max_phrase_seconds: float, clock: CaptureClock | None = None) -> None:
        self.blocks, self.windows, self.warnings, self.stop_event = blocks, windows, warnings, stop_event
        self.frame_samples = 512
        self.pending = np.empty(0, dtype=np.float32)
        self.received = 0
        self.max_phrase_samples = round(max_phrase_seconds * SAMPLE_RATE)
        self.pad_samples = round(pad_seconds * SAMPLE_RATE)
        self.history = np.empty(0, dtype=np.float32)
        self.phrase = np.empty(0, dtype=np.float32)
        self.phrase_start_sample = 0
        self.vad_detected_sample: int | None = None
        self.last_owned_end = 0
        self.iterator_base_sample = 0
        self.iterator = VADIterator(load_silero_vad(onnx=True), threshold=threshold, sampling_rate=SAMPLE_RATE, min_silence_duration_ms=round(silence_seconds * 1000), speech_pad_ms=round(pad_seconds * 1000))
        self.clock = clock or CaptureClock(None)
        self.sequence = 0

    def finish(self, end_sample: int) -> None:
        if len(self.phrase):
            owned_end = max(self.phrase_start_sample, end_sample)
            self.sequence += 1
            self.put_window(audio_window(
                self.phrase.reshape(-1, 1), self.phrase_start_sample, owned_end,
                segment_id=f"segment-{self.sequence}", clock=self.clock,
                vad_detected_sample=self.vad_detected_sample, vad_closed_sample=owned_end,
            ))
            self.last_owned_end = owned_end
        self.phrase = np.empty(0, dtype=np.float32)
        self.vad_detected_sample = None

    def run(self) -> None:
        while not self.stop_event.is_set() or not self.blocks.empty():
            try: block = self.blocks.get(timeout=0.1)
            except queue.Empty: continue
            self.pending = np.concatenate((self.pending, block[:, 0]))
            while len(self.pending) >= self.frame_samples:
                frame, self.pending = self.pending[:self.frame_samples].copy(), self.pending[self.frame_samples:]
                raw_event = self.iterator(frame)
                event = ({key: value + self.iterator_base_sample for key, value in raw_event.items()} if raw_event else None)
                frame_start = self.received; self.received += len(frame)
                self.history = np.concatenate((self.history, frame))[-self.pad_samples:]
                if event and "start" in event:
                    self.phrase_start_sample = max(self.last_owned_end, event["start"])
                    self.vad_detected_sample = event["start"]
                    self.phrase = self.history[:-len(frame)].copy()
                if len(self.phrase): self.phrase = np.concatenate((self.phrase, frame))
                if len(self.phrase) >= self.max_phrase_samples:
                    self.finish(frame_start + len(frame))
                    self.iterator.reset_states()
                    self.iterator_base_sample = self.received
                elif event and "end" in event:
                    self.finish(event["end"])
        self.finish(self.received)


def capture_callback(
    blocks: queue.Queue[np.ndarray],
    warnings: queue.Queue[str],
    input_gain: float = 1.0,
) -> callable:
    def callback(indata: np.ndarray, _frames: int, _time: object, status: sd.CallbackFlags) -> None:
        if status:
            warnings.put(f"Microphone status: {status}")
        try:
            if input_gain == 1.0:
                audio = indata.copy()
            else:
                audio = np.clip(indata * input_gain, -1.0, 1.0)
            blocks.put_nowait(audio)
        except queue.Full:
            warnings.put("Microphone capture is overloaded; discarded an audio block.")

    return callback


def transcribe_windows(
    windows: queue.Queue[AudioWindow],
    warnings: queue.Queue[str],
    stop_event: threading.Event,
    language: str,
    output_format: str,
    silero_vad_model: Path | None = None,
    timebase_ns: int | None = None,
) -> None:
    """Write queued audio to temporary WAV files and emit finalized transcripts."""
    previous = ""
    sequence = 0
    silero_covered_until_ms = 0
    while not stop_event.is_set():
        try:
            window = windows.get(timeout=0.1)
        except queue.Empty:
            continue
        timing = dict(window.timing)
        timestamps = dict(timing.get("timestamps_ns", {}))
        queue_depths = dict(timing.get("queue_depths", {}))
        asr_queue = dict(queue_depths.get("asr", {}))
        asr_queue["dequeue"] = windows.qsize()
        queue_depths["asr"] = asr_queue
        if timebase_ns is not None:
            timestamps["asr_start"] = relative_monotonic_ns(timebase_ns)
        if timing:
            timing["timestamps_ns"] = timestamps
            timing["queue_depths"] = queue_depths
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            window_path = Path(temp_file.name)
        try:
            sf.write(window_path, window.audio, SAMPLE_RATE)
            event_start_ms, event_end_ms = window.start_ms, window.end_ms
            if silero_vad_model is not None:
                segments = new_timed_segments(
                    transcribe_timed(
                        window_path, language, cancel_event=stop_event, silero_vad_model=silero_vad_model
                    ),
                    window.start_ms,
                    silero_covered_until_ms,
                )
                silero_covered_until_ms = max(silero_covered_until_ms, window.end_ms)
                transcript = " ".join(segment.text for segment in segments)
                if segments:
                    event_start_ms, event_end_ms = segments[0].start_ms, segments[-1].end_ms
            else:
                transcript = transcribe(
                    window_path, language, show_status=False, cancel_event=stop_event
                )
            if timebase_ns is not None:
                timestamps["asr_complete"] = relative_monotonic_ns(timebase_ns)
            if transcript:
                new_text = remove_overlap(
                    previous, transcript, trim_single_sentence_word=silero_vad_model is not None
                )
                if new_text:
                    sequence += 1
                    if output_format == "ndjson":
                        segment_id = timing.get("segment_id", f"segment-{sequence}")
                        event = {
                            "id": segment_id,
                            "text": new_text,
                            "start_ms": event_start_ms,
                            "end_ms": event_end_ms,
                        }
                        if timing:
                            event["timing"] = timing
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
    if not MIN_INPUT_GAIN_DB <= args.input_gain_db <= MAX_INPUT_GAIN_DB:
        raise ValueError(
            f"--input-gain-db must be between {MIN_INPUT_GAIN_DB:g} and {MAX_INPUT_GAIN_DB:g}."
        )
    if args.segmentation != "vad" and args.vad_backend != "webrtc":
        raise ValueError("--vad-backend is only valid with --segmentation vad.")
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
    set_demo_process_title()
    args = parse_args()
    try:
        validate_args(args)
        if args.vad_backend == "silero" and not 0 < args.silero_threshold < 1:
            raise ValueError("--silero-threshold must be between 0 and 1.")
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc
    input_gain = 10 ** (args.input_gain_db / 20)
    input_gain_label = f"{args.input_gain_db:+g}" if args.input_gain_db else "0"
    trace_timebase_ns = trace_timebase_from_environment()
    capture_clock = CaptureClock(trace_timebase_ns)

    blocks: queue.Queue[np.ndarray] = queue.Queue(maxsize=100)
    windows: queue.Queue[AudioWindow] = queue.Queue(maxsize=WINDOW_QUEUE_SIZE)
    warnings: queue.Queue[str] = queue.Queue()
    stop_event = threading.Event()
    if args.segmentation == "vad" and args.vad_backend == "webrtc":
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
            capture_clock,
        )
        listening_message = (
            "Listening continuously to the default microphone with local WebRTC VAD "
            f"phrases ending after {args.vad_silence_seconds:g} seconds of silence "
            f"or {args.vad_max_phrase_seconds:g} seconds maximum. Press Ctrl-C to stop."
        )
    elif args.segmentation == "vad":
        segmenter = SileroSegmenter(blocks, windows, warnings, stop_event, args.silero_threshold, args.silero_min_silence_seconds, args.silero_speech_pad_seconds, args.silero_max_phrase_seconds, capture_clock)
        listening_message = (
            "Listening continuously with stateful local Silero VAD "
            f"at confidence {args.silero_threshold:g}. "
            "Press Ctrl-C to stop."
        )
    else:
        segmenter = WindowSegmenter(
            blocks, windows, warnings, stop_event, args.window_seconds, args.stride_seconds, capture_clock
        )
        listening_message = (
            "Listening continuously to the default microphone "
            f"with {args.window_seconds:g}-second windows every {args.stride_seconds:g} seconds. "
            "Press Ctrl-C to stop."
        )
    segmenter_thread = threading.Thread(target=segmenter.run, name="audio-segmenter")
    worker_thread = threading.Thread(
        target=transcribe_windows,
        args=(windows, warnings, stop_event, args.language, args.output_format, None, trace_timebase_ns),
        name="whisper-worker",
    )
    segmenter_thread.start()
    worker_thread.start()

    started_at = time.monotonic()
    print(f"{listening_message} Input gain: {input_gain_label} dB.", file=sys.stderr)
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=round(BLOCK_SECONDS * SAMPLE_RATE),
            callback=capture_callback(blocks, warnings, input_gain),
        ):
            capture_clock.started_ns = time.monotonic_ns()
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
