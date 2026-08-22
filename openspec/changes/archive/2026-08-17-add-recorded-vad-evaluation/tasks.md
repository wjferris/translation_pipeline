## 1. Evaluation scaffold

- [x] 1.1 Add a non-package developer evaluator that validates and reads a 16 kHz mono WAV into source-timestamped blocks without opening an audio device.
- [x] 1.2 Adapt the existing WebRTC VAD phrase segmentation path for deterministic file replay and locally transcribe every finalized phrase.
- [x] 1.3 Adapt the existing Silero windowing, local Whisper invocation, and overlap reconciliation path for file replay, with early prerequisite validation.
- [x] 1.4 Add explicit backend selection, input/output paths, overwrite protection, optional source trim, and existing VAD tuning controls to the evaluator interface.

## 2. Artifacts and comparison

- [x] 2.1 Write timestamped per-backend NDJSON transcripts and a run manifest recording input, backend, models, and effective options.
- [x] 2.2 Parse an English SRT reference and generate a readable, explicitly approximate normalized-text comparison report with source timing.
- [x] 2.3 Add a developer shell launcher that runs one requested backend or both backends against the same WAV/SRT inputs into separate artifact directories.
- [x] 2.4 Add ignore rules for the extracted recording, subtitle fixture, and generated evaluation artifacts while retaining a documented reproducible extraction command.

## 3. Verification and documentation

- [x] 3.1 Add unit tests for WAV validation, replay timestamping, SRT parsing, artifact overwrite protection, and report generation.
- [x] 3.2 Add tests using mocked local transcription for WebRTC phrase emission and Silero overlap de-duplication, without requiring model inference.
- [x] 3.3 Document the fixture-preparation command, single-backend evaluation, both-backend comparison flow, expected artifacts, and the limits of subtitle-based comparison.
- [x] 3.4 Run the relevant test suite and one local smoke test for each backend when the local model prerequisites are available.
