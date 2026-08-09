## ADDED Requirements

### Requirement: Transcribe with local Whisper
The system SHALL provide a `transcribe-whisper` command that invokes the locally installed Whisper CLI with the configured local model and prints the English transcript to standard output.

#### Scenario: Successful local transcription
- **WHEN** a user runs `uv run transcribe-whisper path/to/english-audio.mp3` with Whisper and its model installed
- **THEN** the command SHALL produce the transcript without contacting Hugging Face or downloading model files

#### Scenario: Missing Whisper installation
- **WHEN** the Whisper executable or configured model file is unavailable
- **THEN** the command SHALL exit with a non-zero status and identify the missing local prerequisite
