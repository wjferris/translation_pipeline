## MODIFIED Requirements

### Requirement: Transcribe a local audio file
The system SHALL provide a `transcribe-whisper` command that accepts zero or one path to a local audio file and produces an English Whisper transcription. When no path is supplied, it SHALL use the bundled full `voxtral-winning-call.mp3` sample.

#### Scenario: Successful transcription
- **WHEN** a user runs `uv run transcribe-whisper path/to/english-audio.wav` with a readable supported audio file
- **THEN** the command SHALL print the resulting English transcript to standard output and exit successfully

#### Scenario: Default sample transcription
- **WHEN** a user runs `uv run transcribe-whisper` without an audio path
- **THEN** the command SHALL transcribe `src/resources/voxtral-winning-call.mp3`

#### Scenario: Missing audio file
- **WHEN** a user supplies a path that does not identify a readable file
- **THEN** the command SHALL exit with a non-zero status and explain the input error on standard error
