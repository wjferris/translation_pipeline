## 1. Local VAD segmentation

- [x] 1.1 Confirm a clean committed Git baseline before altering code, dependencies, or documentation.
- [x] 1.2 Add and verify the local WebRTC VAD dependency on the development environment.
- [x] 1.3 Add `--segmentation fixed|vad`, preserving fixed Medium 5/4 as the default.
- [x] 1.4 Implement continuous 16 kHz frame-based VAD phrase segmentation with configurable pre-roll, silence end, minimum phrase, and maximum phrase limits.
- [x] 1.5 Preserve phrase sequence/timing and existing readable-text and NDJSON output behavior.

## 2. Documentation and evaluation

- [x] 2.1 Document VAD mode, its settings, expected pause latency, and the unchanged fixed-window fallback.
- [x] 2.2 Add focused segmentation tests for speech pause, maximum-duration split, short-noise discard, and stop/end flush.
- [x] 2.3 Compare VAD and fixed modes using the same controlled church-talk reading; record accuracy, translation context, duplicate fragments, and perceived delay.

## 3. Validation

- [x] 3.1 Verify VAD NDJSON output flows through `buffer-phrases` and `translate-stream`.
- [x] 3.2 Validate the completed OpenSpec change artifacts.
