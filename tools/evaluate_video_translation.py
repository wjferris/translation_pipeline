#!/usr/bin/env python3
"""Compare the local live translation pipeline with a paired Spanish video.

The English video's audio is replayed through the recorded VAD/Whisper path,
then each recognized event is translated with the same Ollama worker model.
The Spanish video's embedded subtitle track is used as the human-produced
baseline.  Generated artifacts are intentionally kept outside the repository.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from difflib import SequenceMatcher

import soundfile as sf
from ollama import Client

from evaluate_recorded_vad import (
    EvaluationEvent,
    SubtitleCue,
    comparison_report,
    normalize,
    parse_srt,
    prepare_output,
    replay_silero_windows,
    replay_webrtc_windows,
    read_wav,
)
from live_audio_translation.phrase_context import (
    DEFAULT_TRANSLATION_CONTEXT_PHRASES,
    DEFAULT_WHISPER_CONTEXT_PHRASES,
    EnglishContext,
    TranslationContext,
)
from live_audio_translation.transcribe_microphone import AudioWindow, remove_overlap
from live_audio_translation.transcribe_whisper import transcribe
from live_audio_translation.translate_stream import DEFAULT_MODEL, translate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("english_video", type=Path, help="Paired English MP4")
    parser.add_argument("spanish_video", type=Path, help="Paired Spanish MP4 with baseline subtitles")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--vad-backend", choices=("webrtc", "silero"), default="webrtc")
    parser.add_argument(
        "--whisper-context-phrases", type=int, default=DEFAULT_WHISPER_CONTEXT_PHRASES,
        help="Prior finalized English phrases supplied to Whisper (default: 1; 0 disables).",
    )
    parser.add_argument(
        "--translation-context-phrases", type=int, default=DEFAULT_TRANSLATION_CONTEXT_PHRASES,
        help="Completed English/Spanish pairs supplied to TranslationGemma (default: 2; 0 disables).",
    )
    parser.add_argument("--no-gpu", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--vad-aggressiveness", type=int, default=2)
    parser.add_argument("--vad-silence-seconds", type=float, default=0.7)
    parser.add_argument("--vad-pre-roll-seconds", type=float, default=0.3)
    parser.add_argument("--vad-min-phrase-seconds", type=float, default=0.7)
    parser.add_argument("--vad-max-phrase-seconds", type=float, default=10.0)
    parser.add_argument("--silero-threshold", type=float, default=0.5)
    parser.add_argument("--silero-min-silence-seconds", type=float, default=0.3)
    parser.add_argument("--silero-speech-pad-seconds", type=float, default=0.1)
    parser.add_argument("--silero-max-phrase-seconds", type=float, default=10.0)
    return parser.parse_args()


def run_ffmpeg(arguments: list[str]) -> None:
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, check=False)
    except OSError as error:
        raise ValueError(f"Cannot run ffmpeg: {error}") from error
    if result.returncode:
        raise ValueError(result.stderr.strip() or "ffmpeg failed")


def extract_audio(video: Path, wav: Path) -> None:
    if not video.is_file():
        raise ValueError(f"Video not found or unreadable: {video}")
    run_ffmpeg([
        "ffmpeg", "-v", "error", "-y", "-i", str(video), "-map", "0:a:0",
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav),
    ])


def extract_subtitles(video: Path, srt: Path) -> None:
    run_ffmpeg([
        "ffmpeg", "-v", "error", "-y", "-i", str(video), "-map", "0:s:0",
        "-c:s", "srt", str(srt),
    ])


def evaluate_events(
    windows: list[AudioWindow], *, no_gpu: bool, whisper_context_phrases: int
) -> list[EvaluationEvent]:
    """Transcribe replay windows with the same bounded prior-English context as live ASR."""
    context = EnglishContext(whisper_context_phrases)
    previous = ""
    events: list[EvaluationEvent] = []
    for window in windows:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary:
            path = Path(temporary.name)
        try:
            sf.write(path, window.audio, 16_000)
            transcript = transcribe(
                path, "en", show_status=False, no_gpu=no_gpu, prompt=context.prompt()
            )
        finally:
            path.unlink(missing_ok=True)
        new_text = remove_overlap(previous, transcript)
        if new_text:
            events.append(EvaluationEvent(f"segment-{len(events) + 1}", new_text, window.start_ms, window.end_ms))
            context.add(new_text)
        previous = transcript
    return events


def translate_events(
    events: list[EvaluationEvent], model: str, translation_context_phrases: int
) -> list[EvaluationEvent]:
    client = Client()
    context = TranslationContext(translation_context_phrases)
    translated: list[EvaluationEvent] = []
    for event in events:
        text = translate(client, model, event.text, context=context)
        translated.append(EvaluationEvent(event.id, text, event.start_ms, event.end_ms))
        context.add(event.text, text)
    return translated


def translation_report(cues: list[SubtitleCue], events: list[EvaluationEvent], backend: str, model: str) -> str:
    baseline = " ".join(cue.text for cue in cues)
    generated = " ".join(event.text for event in events)
    similarity = SequenceMatcher(None, normalize(baseline), normalize(generated)).ratio()
    event_similarities = []
    for event in events:
        reference = " ".join(
            cue.text for cue in cues if cue.end_ms > event.start_ms and cue.start_ms < event.end_ms
        )
        if reference:
            event_similarities.append(SequenceMatcher(None, normalize(reference), normalize(event.text)).ratio())
    mean_event_similarity = statistics.mean(event_similarities) if event_similarities else 0.0
    median_event_similarity = statistics.median(event_similarities) if event_similarities else 0.0
    report = comparison_report(cues, events, backend)
    return report.replace(
        f"# Recorded VAD evaluation: {backend}",
        f"# Video translation evaluation: {backend}",
        1,
    ).replace(
        "This is an approximate normalized-text comparison. Embedded subtitles can paraphrase speech or use different timing.",
        "This compares pipeline Spanish output with the embedded Spanish subtitle baseline. Subtitle timing can differ between the paired videos.",
        1,
    ).replace(
        "## Summary",
        f"## Summary\n\n- Translation model: `{model}`\n- Pipeline Spanish events: {len(events)}\n- Whole-document normalized text similarity: {similarity:.1%}\n- Mean per-event normalized similarity: {mean_event_similarity:.1%}\n- Median per-event normalized similarity: {median_event_similarity:.1%}",
        1,
    )


def write_events(path: Path, events: list[EvaluationEvent]) -> None:
    path.write_text("".join(json.dumps(asdict(event), ensure_ascii=False) + "\n" for event in events), encoding="utf-8")


def validate_args(args: argparse.Namespace) -> None:
    if not 0 <= args.vad_aggressiveness <= 3:
        raise ValueError("--vad-aggressiveness must be between 0 and 3.")
    if args.whisper_context_phrases < 0:
        raise ValueError("--whisper-context-phrases must be zero or greater.")
    if args.translation_context_phrases < 0:
        raise ValueError("--translation-context-phrases must be zero or greater.")
    if any(getattr(args, option) <= 0 for option in (
        "vad_silence_seconds", "vad_pre_roll_seconds", "vad_min_phrase_seconds", "vad_max_phrase_seconds",
        "silero_threshold", "silero_min_silence_seconds", "silero_speech_pad_seconds", "silero_max_phrase_seconds",
    )):
        raise ValueError("VAD duration and threshold options must be greater than zero.")


def main() -> None:
    args = parse_args()
    try:
        validate_args(args)
        prepare_output(args.output_dir, args.overwrite)
        with tempfile.TemporaryDirectory(prefix="video-translation-") as directory:
            temp = Path(directory)
            english_wav = temp / "english.wav"
            spanish_srt = args.output_dir / "baseline-spanish.srt"
            extract_audio(args.english_video, english_wav)
            extract_subtitles(args.spanish_video, spanish_srt)
            audio = read_wav(english_wav)
            replay_args = argparse.Namespace(**vars(args))
            if args.vad_backend == "webrtc":
                windows = replay_webrtc_windows(audio, 0, replay_args)
            else:
                windows = replay_silero_windows(audio, 0, replay_args)
            asr_started = time.monotonic()
            events = evaluate_events(
                windows, no_gpu=args.no_gpu, whisper_context_phrases=args.whisper_context_phrases
            )
            asr_seconds = time.monotonic() - asr_started
            translation_started = time.monotonic()
            translated = translate_events(events, args.model, args.translation_context_phrases)
            translation_seconds = time.monotonic() - translation_started
        cues = parse_srt(spanish_srt)
        write_events(args.output_dir / "english-transcript.ndjson", events)
        write_events(args.output_dir / "pipeline-spanish.ndjson", translated)
        (args.output_dir / "comparison.md").write_text(
            translation_report(cues, translated, args.vad_backend, args.model), encoding="utf-8"
        )
        manifest = {
            "english_video": str(args.english_video.resolve()),
            "spanish_video": str(args.spanish_video.resolve()),
            "baseline": "embedded Spanish subtitle track",
            "vad_backend": args.vad_backend,
            "model": args.model,
            "whisper_context_phrases": args.whisper_context_phrases,
            "translation_context_phrases": args.translation_context_phrases,
            "pipeline_events": len(translated),
            "timing_seconds": {
                "asr": round(asr_seconds, 3),
                "translation": round(translation_seconds, 3),
                "total_model_processing": round(asr_seconds + translation_seconds, 3),
            },
        }
        (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote video translation evaluation to {args.output_dir}", file=sys.stderr)
    except (ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
