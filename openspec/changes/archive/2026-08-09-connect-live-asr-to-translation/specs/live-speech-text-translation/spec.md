## ADDED Requirements

### Requirement: Stream live English transcription to Spanish text translation
The system SHALL support a local standard-stream pipeline in which finalized English NDJSON events from `transcribe-microphone --output-format ndjson` are accepted by `translate-stream` and emitted as Spanish NDJSON events.

#### Scenario: Run the local microphone-to-Spanish-text flow
- **WHEN** a user runs `uv run transcribe-microphone --output-format ndjson | uv run translate-stream` with microphone permission, a usable local Whisper installation, and local Ollama TranslateGemma available
- **THEN** finalized microphone speech SHALL be emitted from the pipeline as Spanish JSON events while both processes remain active

### Requirement: Keep live translation stages observable
The ASR stage SHALL write its readable English transcript and operational diagnostics to standard error in NDJSON mode, while the final pipeline standard output contains only Spanish translation JSON events.

#### Scenario: Inspect English while consuming Spanish events
- **WHEN** the microphone-to-Spanish-text pipeline processes a finalized transcript
- **THEN** an operator SHALL be able to observe the English text on standard error without invalidating the Spanish JSON stream on standard output
