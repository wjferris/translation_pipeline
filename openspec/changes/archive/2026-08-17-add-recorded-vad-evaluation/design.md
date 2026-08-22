## Context

`transcribe-microphone` owns the current runtime VAD paths: Python/WebRTC
segments callback-captured audio before transcription, while Silero is invoked
inside `whisper.cpp` on overlapping capture windows. Those paths cannot accept
a recording without an audio device. The extracted Kearon fixture is a 16 kHz
mono WAV and has an English SRT track, so it can make comparison repeatable.

The evaluator is developer tooling, not an application feature. It must reuse
the production segmentation and local ASR adapters where practical so that its
results reflect the actual live paths, but it must not change the demo launcher,
microphone command, browser, translation, or TTS flow.

## Goals / Non-Goals

**Goals:**

- Provide one local command that accepts a WAV and SRT reference and runs either
  `webrtc` or `silero`, with a convenience flow that runs both.
- Produce per-backend NDJSON results with transcript text and source-relative
  timestamps, plus a deterministic readable comparison report against SRT text.
- Preserve backend semantics: WebRTC receives replayed fixed-duration blocks;
  Silero uses the same overlapping Whisper-window and timestamp reconciliation
  approach as live capture.
- Validate input format and Silero prerequisites before a long evaluation run.

**Non-Goals:**

- Changing production live-audio behavior, adding a new application command,
  or routing recorded audio through translation/TTS.
- Defining a single authoritative word-error score or treating subtitle timing
  as perfect verbatim ground truth.
- Committing the large extracted media fixture or generated reports to Git.

## Decisions

### Keep orchestration in developer tooling, not `src/live_audio_translation`

Add a Python evaluator under a non-package developer-tool location and invoke
it through `scripts/evaluate-recorded-vad`. The shell script loads the existing
local environment and calls `uv run python` with explicit arguments. This
keeps the installed application surface unchanged while allowing the evaluator
to import shared VAD/Whisper helpers.

Alternative: add a `transcribe-recording` project command. Rejected because it
would imply a supported application workflow instead of an experiment.

### Replay WAV blocks to reuse WebRTC phrase segmentation

The evaluator reads 16 kHz mono WAV data and feeds 100 ms blocks into the
existing `VADSegmenter` input queue. It drains finalized `AudioWindow` phrases
and transcribes them with the shared Whisper adapter. The evaluator preserves
source positions rather than wall-clock timing, so replay is fast and
deterministic.

Alternative: implement a separate offline WebRTC scanner. Rejected because it
would duplicate phrase-boundary logic and weaken the comparison with live
behavior.

### Use the live Silero window/reconciliation path with file-fed audio

For Silero, the evaluator creates the same window sizes and overlap used by
the live Silero worker, invokes the shared `transcribe_timed` adapter with the
Silero asset, and applies the existing timing-based de-duplication logic. The
result is emitted as finalized source-relative segments.

Alternative: ask Whisper to transcribe the full file once with `--vad`.
Rejected because that would not exercise the live windowing and overlap logic
being evaluated.

### Make NDJSON the canonical artifact; derive a compact report

Each backend writes a separate NDJSON file with `id`, `start_ms`, `end_ms`, and
`text`. A report generator parses the supplied SRT, normalizes text only for a
clearly labeled approximate comparison, and presents reference and recognized
text with timing/coverage summaries. Raw transcript text remains available for
human review.

Alternative: output only console text. Rejected because it is not repeatable
or easy to diff across tuning runs.

### Require explicit artifact locations

The runner requires an output directory (or creates a timestamped directory
under an ignored evaluation-artifacts root) and never overwrites a prior run
without an explicit overwrite switch. The repository ignore rules exclude WAV,
SRT, and generated evaluation artifacts for this fixture.

## Risks / Trade-offs

- [Fast replay can fill queues differently than real-time capture] → drain
  produced windows synchronously and test that the entire input reaches the
  transcription work rather than dropping windows.
- [Silero output depends on the installed Whisper build/model] → record the
  CLI path, ASR model, Silero model, and evaluation options in a run manifest.
- [Subtitles can differ from spoken words] → label metrics as approximate and
  retain timestamped source/reference text for manual assessment.
- [Long files take substantial local ASR time] → support an explicit start/end
  trim option for iteration while retaining full-file evaluation as the default.

## Migration Plan

1. Add the evaluator, shell launcher, documentation, ignore rules, and tests.
2. Run the provided extracted WAV through each backend to verify the flow.
3. No deployment or production migration is required; deleting the developer
   tooling fully rolls back the change.

## Open Questions

- None; default evaluation tuning will mirror the documented live VAD defaults,
  while the launcher exposes their existing tuning flags for experiments.
