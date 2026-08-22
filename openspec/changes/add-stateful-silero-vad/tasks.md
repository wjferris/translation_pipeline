## 1. Local Silero runtime foundation

- [x] 1.1 Select and document a supported local, stateful Silero runtime and model-asset packaging route for the target macOS environment.
- [ ] 1.2 Add the selected local dependency and model discovery/configuration with actionable validation errors and no network use during transcription.
- [ ] 1.3 Add unit tests for Silero runtime/model discovery, prerequisite validation, and backend-specific argument validation.

## 2. Stateful phrase segmentation

- [x] 2.1 Implement a continuous 16 kHz mono Silero segmenter that preserves detector state across capture frames and emits bounded phrase audio with configurable confidence, silence, pre-roll, post-roll, and maximum-duration behavior.
- [x] 2.2 Define monotonic, non-overlapping source ownership timestamps for adjacent Silero phrases while retaining recognition padding where needed.
- [x] 2.3 Route the `silero` VAD backend through the new segmenter and one Whisper transcription per finalized phrase, while preserving the existing WebRTC path and default.
- [x] 2.4 Retire the integrated-Whisper Silero fixed-window token-timing reconciliation from the live Silero path.
- [ ] 2.5 Add deterministic unit tests for speech start/end, forced phrase limits, padding, timestamp ownership, and absence of duplicate boundary transcript events.

## 3. CLI, demo, and recorded evaluation parity

- [ ] 3.1 Expose and validate documented Silero-specific tuning controls in `transcribe-microphone` and forward them through the demo launcher without changing existing WebRTC options.
- [x] 3.2 Update the recorded VAD evaluator to replay WAV source frames through the same stateful Silero segmenter and transcribe each finalized phrase once.
- [ ] 3.3 Record the local Silero runtime/model identity and effective Silero options in evaluation manifests, retaining separate backend artifacts and overwrite protection.
- [ ] 3.4 Update README guidance to describe the stateful Silero architecture, prerequisites, tuning, and recorded comparison workflow.

## 4. Verification

- [x] 4.1 Run the relevant unit tests for microphone segmentation, backend selection, demo argument forwarding, and recorded evaluation.
- [x] 4.2 Run short and extended GPU-backed recorded evaluations for WebRTC and stateful Silero against the same WAV/SRT fixture; review boundary duplication, transcript coherence, and reports.
- [ ] 4.3 Run a local live microphone smoke test for each backend, verifying clean startup, phrase emission, interruption cleanup, and unchanged downstream NDJSON compatibility.
