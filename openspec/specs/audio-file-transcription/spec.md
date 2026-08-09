# audio-file-transcription Specification

## Purpose
TBD - created by archiving change add-voxtral-transcription. Update Purpose after archive.
## Requirements
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

### Requirement: Preserve machine-readable transcript output
The system SHALL reserve standard output for the transcript and write progress or diagnostic information to standard error.

#### Scenario: Transcript used in a pipeline
- **WHEN** a user redirects standard output from a successful transcription command
- **THEN** the redirected output SHALL contain the transcript without status banners or diagnostic messages

### Requirement: Provide a repeatable example input
The system SHALL include a public audio sample lasting between five and ten seconds that can be passed directly to the transcription command.

#### Scenario: First local experiment
- **WHEN** a user runs the documented command with the bundled sample audio
- **THEN** the command SHALL receive a readable local MP3 input without requiring the user to provide a separate recording

