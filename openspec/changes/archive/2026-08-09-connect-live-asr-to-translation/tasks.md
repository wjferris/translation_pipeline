## 1. Structured ASR events

- [x] 1.1 Add an `--output-format` option to `transcribe-microphone`, retaining its readable-text default.
- [x] 1.2 Carry source-window sequence and approximate timing through the transcription worker.
- [x] 1.3 Emit finalized English NDJSON on standard output in NDJSON mode and mirror readable English to standard error.

## 2. Local pipeline experience

- [x] 2.1 Document the microphone-to-Whisper-to-TranslateGemma shell pipeline, prerequisites, output streams, and Ctrl-C behavior.
- [x] 2.2 Verify ASR NDJSON output with a short microphone run and confirm it is accepted by `translate-stream`.
- [x] 2.3 Verify the final pipeline writes valid Spanish JSON to standard output and English/operator diagnostics only to standard error.

## 3. OpenSpec verification

- [x] 3.1 Validate the completed OpenSpec change artifacts.
