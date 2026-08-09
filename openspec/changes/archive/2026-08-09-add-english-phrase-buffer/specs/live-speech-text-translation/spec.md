## MODIFIED Requirements

### Requirement: Stream live English transcription to Spanish text translation
The system SHALL support a local standard-stream pipeline in which finalized English NDJSON events from `transcribe-microphone --output-format ndjson` are buffered into translation-ready English phrases by `buffer-phrases`, accepted by `translate-stream`, and emitted as Spanish NDJSON events.

#### Scenario: Run the local microphone-to-Spanish-text flow
- **WHEN** a user runs `uv run transcribe-microphone --output-format ndjson | uv run buffer-phrases | uv run translate-stream` with microphone permission, a usable local Whisper installation, and local Ollama TranslateGemma available
- **THEN** finalized microphone speech SHALL be emitted from the pipeline as Spanish JSON events while all processes remain active
