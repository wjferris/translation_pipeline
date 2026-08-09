## 1. Stream worker foundation

- [x] 1.1 Add the Ollama client dependency and `translate-stream` console command.
- [x] 1.2 Implement newline-delimited JSON input validation, ordered event processing, and JSON-only standard output.

## 2. Local translation

- [x] 2.1 Implement local TranslateGemma inference with a fixed English-to-Spanish prompt.
- [x] 2.2 Preserve event identifiers/timing and provide structured error events for inference failures.

## 3. Documentation and verification

- [x] 3.1 Add `src/resources/translation-test-input.ndjson`, with representative final English segments adapted from `narration-script.md`.
- [x] 3.2 Document the stream protocol, local Ollama prerequisites, and pipe usage.
- [x] 3.3 Verify a successful translation using the fixture, plus malformed-input and unavailable-model behavior.
- [x] 3.4 Validate the OpenSpec change artifacts.
