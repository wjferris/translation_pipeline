## Context

The live microphone pipeline currently has two VAD choices. WebRTC continuously segments microphone frames into pause-delimited phrases before each Whisper call. The Silero option instead sends overlapping five-second windows to Whisper's integrated VAD, then remaps compressed token timings and removes overlap after independent recognitions. Recorded evaluation showed fragmented text, repeated boundary words, and lost ASR context.

The application must keep all audio and inference local, preserve the WebRTC default and CLI selector, and keep emitting finalized NDJSON events to the shared phrase-buffer, translation, TTS, and display stages.

## Goals / Non-Goals

**Goals:**

- Provide a continuous, stateful local Silero speech detector that produces bounded phrase audio for one Whisper recognition per phrase.
- Keep WebRTC and stateful Silero as interchangeable implementations behind the existing VAD-backend selector; retain WebRTC behavior by default.
- Use the same stateful Silero phrase behavior in recorded evaluation and live microphone processing, with source-relative, non-duplicated result timing.
- Make local prerequisites and backend-specific tuning actionable and testable.

**Non-Goals:**

- Change the selected Whisper model, Metal/GPU configuration, translation, Piper, browser display, or default WebRTC settings.
- Make fixed-window transcription stateful or remove it.
- Replace WebRTC as the default without successful recorded and live evaluation.
- Upload audio or depend on a remote VAD service.

## Decisions

### Run Silero independently of Whisper and retain state across capture frames

Add a local Silero runtime/model adapter that accepts continuous 16 kHz mono frames and preserves detector state for the duration of a run. The adapter marks speech start/end using its confidence, silence, padding, and maximum-phrase controls, then enqueues one complete phrase for Whisper.

This replaces `whisper.cpp --vad` as the live Silero implementation. That integration is mature within one Whisper invocation, but this application restarts it for overlapping files and cannot preserve speech context. A local ONNX-capable Silero runtime is preferred over a large Torch-only runtime, subject to packaging verification; VAD inference is CPU-light and does not alter Whisper's Metal use.

### Preserve one shared downstream pipeline and one backend selector

`webrtc` and `silero` remain choices of the phrase-segmenter component. Both emit the same phrase ownership contract and use the existing single Whisper worker, NDJSON event shape, phrase buffer, translator, Piper, and display. The launcher continues passing `--vad-backend` through unchanged.

Duplicating end-to-end pipelines was rejected because it would confound comparisons with different translation or display behavior.

### Separate recognition padding from emitted phrase ownership

Silero may retain short audio before and after detected speech as recognition context. Each emitted event will nevertheless own one monotonic, non-overlapping speech interval. This eliminates the current JSON-token timing remapping and cross-window text reconstruction path.

### Mirror the live segmenter in recorded evaluation

The developer evaluator will feed source WAV frames through the same stateful Silero segmenter used by capture, without opening audio devices. It will retain the per-backend artifact layout and record the selected local VAD runtime/model and effective options in its manifest.

## Risks / Trade-offs

- [A local Silero runtime/model is unavailable or hard to package on the target Mac] → Validate prerequisites before capture or evaluation, document installation, and retain WebRTC as the working default.
- [Thresholds split quiet or noisy speech poorly] → Expose bounded Silero-specific controls, preserve sensible defaults, and compare recorded fixtures before changing defaults.
- [Long continuous speech increases latency] → Enforce a configurable maximum phrase duration with continuity-preserving carryover and short recognition padding.
- [Padding makes neighboring ASR text look similar] → Report non-overlapping ownership timestamps and test that emitted events do not duplicate fully covered words.
- [The new adapter regresses live reliability] → Retain WebRTC unchanged, add deterministic replay tests, and make rollback a backend-selector change.

## Migration Plan

1. Add and validate the local Silero runtime/model adapter without changing the default backend.
2. Implement the stateful Silero phrase segmenter for microphone and recorded replay paths.
3. Remove the retired integrated-Whisper Silero window reconciliation after its replacement has equivalent test coverage.
4. Run short and extended recorded comparisons plus a local live smoke test; retain `webrtc` as default unless a later change revises that decision.

Rollback is immediate by selecting `--vad-backend webrtc`; code rollback restores the existing implementation while leaving the shared downstream pipeline untouched.

## Open Questions

- Which supported local Silero packaging route is most reliable on the target Mac: ONNX Runtime or the official Torch wrapper?
- What defaults for confidence, phrase-end silence, padding, and maximum phrase duration best balance latency and recognition context?
