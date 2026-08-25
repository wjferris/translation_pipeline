## 1. Whisper prior-phrase context

- [x] 1.1 Extend the shared Whisper command adapter to accept and pass a
  bounded optional decoder prompt without changing current file-transcription
  defaults.
- [x] 1.2 Add microphone-worker context settings, initialize per-session
  finalized-English history, and pass the selected prior text to each later
  Whisper request.
- [x] 1.3 Update ASR history only after overlap reconciliation and successful
  emission; exclude discarded and non-speech results.
- [x] 1.4 Forward Whisper context settings through demo mode and report the
  effective non-sensitive configuration at startup and in applicable traces.

## 2. Translation conversation context

- [x] 2.1 Add translation-worker context settings and a bounded per-process
  history of completed English/Spanish phrase pairs.
- [x] 2.2 Build Ollama chat messages from the stable translation instruction,
  selected completed pairs, and the current phrase while emitting only the
  current Spanish result.
- [x] 2.3 Add a successful translation pair to history only after a non-empty
  result is emitted; exclude invalid inputs and failed translations.
- [x] 2.4 Forward translation context settings through demo mode and report the
  effective non-sensitive configuration at startup and in applicable traces.

## 3. Verification and documentation

- [x] 3.1 Add unit tests for context ordering, bounds, zero-value disabling,
  reset behavior, and exclusion of unsuccessful or discarded text.
- [x] 3.2 Add command and demo integration tests confirming the new options are
  forwarded without changing the existing NDJSON contract.
- [x] 3.3 Document the context controls, defaults, privacy behavior, and
  disable/rollback path in the README.
- [x] 3.4 Run the paired-video translation evaluation with context disabled and
  enabled; record semantic-review and timing differences in the trial notes.
