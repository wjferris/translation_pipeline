#!/usr/bin/env python3
"""Developer-only replay harness for comparing local VAD backends.

This module deliberately lives outside the installed application package.  It
reads a recording as quickly as possible, preserves source-relative timing,
and reuses the live VAD/Whisper helpers without opening an audio device.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import soundfile as sf

from live_audio_translation.transcribe_microphone import (
    AudioWindow,
    BLOCK_SECONDS,
    SAMPLE_RATE,
    VADSegmenter,
    SileroSegmenter,
    WindowSegmenter,
    new_timed_segments,
    remove_overlap,
)
from live_audio_translation.transcribe_whisper import (
    TranscriptSegment,
    default_whisper_model,
    transcribe,
    transcribe_timed,
    validate_silero_vad,
    whisper_command,
)


@dataclass(frozen=True)
class SubtitleCue:
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class EvaluationEvent:
    id: str
    text: str
    start_ms: int
    end_ms: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path, help="16 kHz mono WAV recording to replay")
    parser.add_argument("--reference-srt", type=Path, required=True, help="English SRT reference")
    parser.add_argument("--vad-backend", choices=("webrtc", "silero"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true", help="Allow writing into an existing empty directory")
    parser.add_argument("--language", default="en")
    parser.add_argument("--start-seconds", type=float, default=0.0)
    parser.add_argument("--end-seconds", type=float)
    parser.add_argument("--window-seconds", type=float, default=5.0)
    parser.add_argument("--stride-seconds", type=float, default=4.0)
    parser.add_argument("--silero-threshold", type=float, default=0.5)
    parser.add_argument("--silero-min-silence-seconds", type=float, default=0.3)
    parser.add_argument("--silero-speech-pad-seconds", type=float, default=0.1)
    parser.add_argument("--silero-max-phrase-seconds", type=float, default=10.0)
    parser.add_argument("--no-gpu", action="store_true", help="Run Whisper on CPU for this evaluation")
    parser.add_argument("--vad-aggressiveness", type=int, default=2)
    parser.add_argument("--vad-silence-seconds", type=float, default=0.7)
    parser.add_argument("--vad-pre-roll-seconds", type=float, default=0.3)
    parser.add_argument("--vad-min-phrase-seconds", type=float, default=0.7)
    parser.add_argument("--vad-max-phrase-seconds", type=float, default=10.0)
    return parser.parse_args()


def read_wav(path: Path) -> np.ndarray:
    """Read one supported fixture WAV as a column-shaped float32 array."""
    if not path.is_file():
        raise ValueError(f"Audio file not found or unreadable: {path}")
    try:
        with sf.SoundFile(path) as audio:
            if audio.samplerate != SAMPLE_RATE or audio.channels != 1 or audio.format != "WAV":
                raise ValueError("Recorded VAD evaluation requires a 16 kHz mono WAV input.")
            samples = audio.read(dtype="float32", always_2d=True)
    except RuntimeError as error:
        raise ValueError(f"Cannot read WAV input {path}: {error}") from error
    if len(samples) == 0:
        raise ValueError("Recorded VAD evaluation requires a non-empty WAV input.")
    return samples


def select_source_range(audio: np.ndarray, start_seconds: float, end_seconds: float | None) -> tuple[np.ndarray, int]:
    if start_seconds < 0 or (end_seconds is not None and end_seconds <= start_seconds):
        raise ValueError("--start-seconds must be non-negative and less than --end-seconds.")
    start = round(start_seconds * SAMPLE_RATE)
    end = len(audio) if end_seconds is None else min(round(end_seconds * SAMPLE_RATE), len(audio))
    if start >= len(audio) or end <= start:
        raise ValueError("Selected source range contains no audio.")
    return audio[start:end], start


def iter_blocks(audio: np.ndarray) -> Iterable[np.ndarray]:
    block_samples = round(BLOCK_SECONDS * SAMPLE_RATE)
    for offset in range(0, len(audio), block_samples):
        yield audio[offset : offset + block_samples]


def replay_webrtc_windows(audio: np.ndarray, source_start_sample: int, args: argparse.Namespace) -> list[AudioWindow]:
    """Feed fixed source blocks through the live WebRTC VAD implementation."""
    import queue
    import threading

    windows: queue.Queue[AudioWindow] = queue.Queue()
    segmenter = VADSegmenter(
        queue.Queue(), windows, queue.Queue(), threading.Event(), args.vad_aggressiveness,
        args.vad_silence_seconds, args.vad_pre_roll_seconds, args.vad_min_phrase_seconds,
        args.vad_max_phrase_seconds,
    )
    for block in iter_blocks(audio):
        segmenter.pending = np.concatenate((segmenter.pending, block[:, 0]))
        while len(segmenter.pending) >= segmenter.frame_samples:
            frame = segmenter.pending[: segmenter.frame_samples].copy()
            segmenter.pending = segmenter.pending[segmenter.frame_samples :]
            frame_start = segmenter.received
            segmenter.received += segmenter.frame_samples
            segmenter.process_frame(frame, frame_start)
    if segmenter.phrase_frames:
        segmenter.finish_phrase(segmenter.received)

    result: list[AudioWindow] = []
    while not windows.empty():
        window = windows.get_nowait()
        result.append(
            AudioWindow(
                window.audio,
                window.start_ms + round(source_start_sample * 1000 / SAMPLE_RATE),
                window.end_ms + round(source_start_sample * 1000 / SAMPLE_RATE),
            )
        )
    return result


def replay_silero_windows(audio: np.ndarray, source_start_sample: int, args: argparse.Namespace) -> list[AudioWindow]:
    import queue
    import threading
    blocks: queue.Queue[np.ndarray] = queue.Queue()
    windows: queue.Queue[AudioWindow] = queue.Queue()
    stop = threading.Event()
    for block in iter_blocks(audio): blocks.put(block)
    stop.set()
    segmenter = SileroSegmenter(blocks, windows, queue.Queue(), stop, args.silero_threshold, args.silero_min_silence_seconds, args.silero_speech_pad_seconds, args.silero_max_phrase_seconds)
    segmenter.run()
    return [AudioWindow(window.audio, window.start_ms + round(source_start_sample * 1000 / SAMPLE_RATE), window.end_ms + round(source_start_sample * 1000 / SAMPLE_RATE)) for window in list(windows.queue)]


def _write_window(window: AudioWindow) -> Path:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary:
        path = Path(temporary.name)
    sf.write(path, window.audio, SAMPLE_RATE)
    return path


def evaluate_webrtc(
    windows: Iterable[AudioWindow], language: str, *, no_gpu: bool = False,
    transcribe_fn: Callable[..., str] = transcribe,
) -> list[EvaluationEvent]:
    previous = ""
    events: list[EvaluationEvent] = []
    for window in windows:
        path = _write_window(window)
        try:
            transcript = transcribe_fn(path, language, show_status=False, no_gpu=no_gpu)
        finally:
            path.unlink(missing_ok=True)
        new_text = remove_overlap(previous, transcript)
        if new_text:
            events.append(EvaluationEvent(f"segment-{len(events) + 1}", new_text, window.start_ms, window.end_ms))
        previous = transcript
    return events


def evaluate_silero(windows: Iterable[AudioWindow], language: str, *, no_gpu: bool = False) -> list[EvaluationEvent]:
    return evaluate_webrtc(windows, language, no_gpu=no_gpu)


_TIME = re.compile(r"(\d\d):(\d\d):(\d\d),(\d\d\d)")


def _time_ms(value: str) -> int:
    match = _TIME.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"Invalid SRT timestamp: {value}")
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    return (((hours * 60 + minutes) * 60) + seconds) * 1000 + milliseconds


def parse_srt(path: Path) -> list[SubtitleCue]:
    if not path.is_file():
        raise ValueError(f"Subtitle reference not found or unreadable: {path}")
    try:
        blocks = re.split(r"\r?\n\s*\r?\n", path.read_text(encoding="utf-8").strip())
    except OSError as error:
        raise ValueError(f"Cannot read subtitle reference {path}: {error}") from error
    cues: list[SubtitleCue] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or " --> " not in lines[1]:
            raise ValueError(f"Invalid SRT cue in {path}: {block[:80]!r}")
        start, end = lines[1].split(" --> ", 1)
        cues.append(SubtitleCue(_time_ms(start), _time_ms(end.split()[0]), " ".join(lines[2:])))
    return cues


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[\w']+", text.lower()))


def overlapping_reference(cues: Iterable[SubtitleCue], start_ms: int, end_ms: int) -> str:
    return " ".join(cue.text for cue in cues if cue.end_ms > start_ms and cue.start_ms < end_ms)


def format_time(milliseconds: int) -> str:
    seconds, millis = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"


def comparison_report(cues: list[SubtitleCue], events: list[EvaluationEvent], backend: str) -> str:
    relevant_cues = cues
    if events:
        relevant_cues = [
            cue for cue in cues
            if cue.end_ms > min(event.start_ms for event in events)
            and cue.start_ms < max(event.end_ms for event in events)
        ]
    reference = " ".join(cue.text for cue in relevant_cues)
    recognized = " ".join(event.text for event in events)
    similarity = SequenceMatcher(None, normalize(reference), normalize(recognized)).ratio()
    lines = [
        f"# Recorded VAD evaluation: {backend}",
        "",
        "This is an approximate normalized-text comparison. Embedded subtitles can paraphrase speech or use different timing.",
        "",
        "## Summary",
        "",
        f"- Reference cues in evaluated timeline: {len(relevant_cues)}",
        f"- Recognized segments: {len(events)}",
        f"- Approximate normalized character similarity: {similarity:.1%}",
        "",
        "## Timeline",
        "",
    ]
    for event in events:
        reference_text = overlapping_reference(cues, event.start_ms, event.end_ms) or "(no overlapping subtitle)"
        lines.extend([
            f"### {format_time(event.start_ms)}–{format_time(event.end_ms)}",
            "", f"Reference: {reference_text}", "", f"Recognized: {event.text}", "",
        ])
    return "\n".join(lines)


def prepare_output(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise ValueError(f"Output directory already contains artifacts: {path}. Use --overwrite to replace files.")
    path.mkdir(parents=True, exist_ok=True)


def write_artifacts(output_dir: Path, events: list[EvaluationEvent], args: argparse.Namespace, silero_model: Path | None) -> None:
    transcript_path = output_dir / "transcript.ndjson"
    if transcript_path.exists() and not args.overwrite:
        raise ValueError(f"Artifact already exists: {transcript_path}. Use --overwrite to replace it.")
    transcript_path.write_text("".join(json.dumps(asdict(event), ensure_ascii=False) + "\n" for event in events), encoding="utf-8")
    model = Path(os.environ.get("WHISPER_MODEL_PATH", default_whisper_model()))
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(), "backend": args.vad_backend,
        "audio": str(args.wav.resolve()), "reference_srt": str(args.reference_srt.resolve()),
        "whisper_executable": whisper_command(), "whisper_model": str(model),
        "silero_vad_runtime": "silero-vad" if args.vad_backend == "silero" else None,
        "options": {key: value for key, value in vars(args).items() if key not in {"wav", "reference_srt", "output_dir"}},
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    (output_dir / "comparison.md").write_text(comparison_report(parse_srt(args.reference_srt), events, args.vad_backend), encoding="utf-8")


def validate_args(args: argparse.Namespace) -> None:
    if args.window_seconds <= 0 or args.stride_seconds <= 0 or args.stride_seconds > args.window_seconds:
        raise ValueError("--window-seconds and --stride-seconds must be positive, with stride no greater than window.")
    if not 0 <= args.vad_aggressiveness <= 3:
        raise ValueError("--vad-aggressiveness must be between 0 and 3.")
    if any(getattr(args, option) <= 0 for option in ("vad_silence_seconds", "vad_pre_roll_seconds", "vad_min_phrase_seconds", "vad_max_phrase_seconds")):
        raise ValueError("All VAD duration options must be greater than zero.")
    if args.vad_min_phrase_seconds > args.vad_max_phrase_seconds:
        raise ValueError("--vad-min-phrase-seconds cannot exceed --vad-max-phrase-seconds.")


def main() -> None:
    args = parse_args()
    try:
        validate_args(args)
        audio = read_wav(args.wav)
        source, source_start = select_source_range(audio, args.start_seconds, args.end_seconds)
        parse_srt(args.reference_srt)
        prepare_output(args.output_dir, args.overwrite)
        if args.vad_backend == "webrtc":
            events = evaluate_webrtc(replay_webrtc_windows(source, source_start, args), args.language, no_gpu=args.no_gpu)
        else:
            events = evaluate_silero(replay_silero_windows(source, source_start, args), args.language, no_gpu=args.no_gpu)
        write_artifacts(args.output_dir, events, args, None)
        print(f"Wrote {len(events)} {args.vad_backend} transcript segments to {args.output_dir}", file=sys.stderr)
    except (ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
