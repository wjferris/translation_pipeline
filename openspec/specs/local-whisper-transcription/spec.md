# local-whisper-transcription Specification

## Purpose
TBD - created by archiving change replace-voxtral-with-whisper. Update Purpose after archive.
## Requirements
### Requirement: Transcribe with local Whisper
The system SHALL provide a `transcribe-whisper` command that invokes the locally installed Whisper CLI with the configured local model and prints the English transcript to standard output. It SHALL default to `/opt/local/share/whisper/models/medium.bin` when no override is supplied, while the project environment SHALL select `/opt/local/share/whisper/models/small.bin` through `WHISPER_MODEL_PATH` for the current comparison experiment.

#### Scenario: Successful local transcription
- **WHEN** a user sources the project `.env` and runs `uv run transcribe-whisper path/to/english-audio.mp3` with Whisper and the Small model installed
- **THEN** the command SHALL produce the transcript with Small without contacting Hugging Face or downloading model files

#### Scenario: Missing Whisper installation
- **WHEN** the Whisper executable or configured model file is unavailable
- **THEN** the command SHALL exit with a non-zero status and identify the missing local prerequisite

#### Scenario: MacPorts library path omission
- **WHEN** a MacPorts Whisper variant lacks its `ggml` runtime library search path
- **THEN** the command SHALL start Whisper with `/opt/local/lib` available as a fallback library path

