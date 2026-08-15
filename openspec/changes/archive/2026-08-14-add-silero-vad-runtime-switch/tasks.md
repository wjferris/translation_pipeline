## 1. Whisper/Silero compatibility discovery

- [x] 1.1 Identify the supported local Whisper executable's integrated Silero VAD flags, output behavior, and required local model asset.
- [x] 1.2 Implement a bounded capability check that reports unsupported executable versions or missing local Silero assets before microphone capture.
- [x] 1.3 Add tests covering supported and unsupported capability-check results without requiring a microphone.

## 2. Runtime VAD backend implementation

- [x] 2.1 Add `--vad-backend` selection to `transcribe-microphone`, defaulting to the existing WebRTC implementation, with validation for segmentation and backend-specific options.
- [x] 2.2 Encapsulate the Whisper-integrated Silero invocation and map its completed local results into the existing final-transcript event path.
- [x] 2.3 Preserve fixed-window mode and current WebRTC VAD behavior, including NDJSON fields, cancellation, and local-only processing.
- [x] 2.4 Forward the VAD-backend option through demo mode and its background launcher.

## 3. Verification and operator guidance

- [x] 3.1 Add unit and integration coverage for backend selection, validation failures, command construction, and final-event compatibility.
- [x] 3.2 Document WebRTC and Silero A/B commands, prerequisites, backend-specific tuning, and fallback guidance in the README.
- [x] 3.3 Run both backend modes against the supported local Whisper installation and record the observed startup, phrase-boundary, and shutdown behavior. WebRTC remained the unchanged baseline; the live Silero confirmation passed after timestamp-boundary reconciliation.
