## Context

`transcribe-microphone` currently implements pause-delimited phrases in Python with WebRTC VAD before passing each phrase to the locally installed Whisper CLI. Demo mode forwards the same segmentation arguments to this worker. The requested experiment needs to retain that known baseline while making a Whisper build's integrated Silero VAD selectable at runtime.

## Goals / Non-Goals

**Goals:**

- Offer a clear runtime backend selector for VAD-based microphone runs and demo mode.
- Keep Python/WebRTC VAD as the default and preserve its existing tuning behavior.
- Invoke integrated Silero VAD only when the installed local Whisper executable demonstrably supports its required flags and assets.
- Make the selected backend visible in startup diagnostics and comparison documentation.

**Non-Goals:**

- No cloud transcription, remote VAD service, or automatic quality scoring.
- No replacement of fixed-window mode, NDJSON compatibility, or the existing phrase-buffer protocol.
- No claim that all Whisper distributions expose the same Silero options; support is explicitly capability-checked.

## Decisions

### Use `--vad-backend` only with VAD segmentation

The microphone CLI will accept a backend selector with `webrtc` as the default and `silero` as the alternative. The option is meaningful only with `--segmentation vad`; fixed-window behavior remains unchanged and rejects or ignores incompatible VAD-only configuration with actionable guidance. Demo mode forwards the selector unchanged.

This makes an A/B command line explicit and preserves existing scripts. Replacing `--segmentation vad` entirely was rejected because it would break the established WebRTC experiment and conflate segmentation mode with implementation choice.

### Isolate Whisper/Silero support behind a local adapter

An adapter will construct the integrated-Silero invocation from the actual installed Whisper CLI contract. Before microphone capture starts, it will inspect or probe the executable for the required VAD flags and verify any required local Silero model asset. If unsupported, it will fail early with the discovered executable limitation and the fallback `--vad-backend webrtc` command.

The exact Whisper command-line flags and output mapping differ across distributions, so hard-coding an assumed interface is rejected. The implementation task begins with a compatibility spike against the project-supported Whisper executable and turns that result into tests.

### Keep comparable event behavior

Both backends will feed the existing final-transcript event path, including NDJSON fields and phrase buffering. Backend-specific phrase timing will be preserved where available, but no artificial attempt will be made to make their boundaries identical.

### Reconcile overlapping Silero windows by timestamp

The live capture path retains its small audio overlap so Whisper has context at
a capture boundary. For integrated Silero runs, the adapter requests
`whisper.cpp` JSON output and maps each returned segment's millisecond offsets
onto the microphone timeline. Tokens whose end is already covered by the
preceding window are suppressed, and emitted events use the retained token
timestamps rather than the full capture-window range.

The supported Whisper build reports full-JSON token offsets in VAD-compressed
time. The adapter calibrates each token sequence onto its enclosing segment's
original-audio range before applying the overlap boundary.

This avoids treating independently decoded text as an exact suffix/prefix
match, while still allowing a segment that crosses the boundary to carry its
recognition context forward.

## Risks / Trade-offs

- [Installed Whisper lacks integrated Silero VAD] → Detect before opening the microphone, explain the missing support, and retain WebRTC as the default fallback.
- [Silero requires a separate model asset] → Document the local asset location/installation and verify it before a run.
- [Backends yield different phrase timing or text boundaries] → Report backend identity and document A/B commands rather than treating results as directly identical.
- [Whisper output differs by distribution] → Encapsulate parsing/command construction and cover the supported contract with fixtures or integration tests.

## Migration Plan

The new backend selector is additive; existing VAD and demo invocations continue to select WebRTC by default. Rollback removes the selector and adapter without changing current VAD segmentation behavior or event formats.

## Open Questions

- Which local Whisper executable/distribution and version is the supported target for its integrated Silero VAD command and model asset contract?
