## Why

The current microphone VAD path uses the Python WebRTC detector, but there is no runtime way to compare its phrase boundaries with Whisper's integrated Silero VAD. A selectable backend will make latency and transcription-quality experiments repeatable without replacing the established local pipeline.

## What Changes

- Add a runtime VAD-backend option for VAD-segmented microphone transcription and the demo launcher.
- Preserve the current Python/WebRTC phrase segmenter as the default backend.
- Add an option that delegates phrase/VAD handling to the local Whisper executable's integrated Silero VAD support when available.
- Report the selected backend and provide clear validation errors when the installed Whisper executable cannot use the requested integrated Silero mode.
- Document equivalent commands and comparison guidance for testing both local VAD paths.

## Capabilities

### New Capabilities

- `runtime-vad-backend-selection`: Select and report the local VAD implementation used for a live transcription run.

### Modified Capabilities

- `voice-activity-phrase-segmentation`: VAD phrase segmentation gains an alternative local Whisper/Silero implementation while retaining the existing configurable Python detector.
- `live-microphone-transcription`: The microphone CLI and demo can select the VAD backend at runtime when VAD segmentation is enabled.

## Impact

- Affects microphone command arguments, demo argument forwarding, local Whisper invocation, dependencies or model assets as required by the installed Whisper distribution, tests, and README guidance.
- Does not change fixed-window transcription, NDJSON event compatibility, cloud usage, or the default VAD backend.
