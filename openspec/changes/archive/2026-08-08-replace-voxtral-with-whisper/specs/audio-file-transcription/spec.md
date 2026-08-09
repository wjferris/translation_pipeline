## MODIFIED Requirements

### Requirement: Transcribe a local audio file
The system SHALL provide a `transcribe-whisper` command that accepts exactly one path to a local audio file and produces an English Whisper transcription.

#### Scenario: Successful transcription
- **WHEN** a user runs `uv run transcribe-whisper path/to/english-audio.wav` with a readable supported audio file
- **THEN** the command SHALL print the resulting English transcript to standard output and exit successfully

#### Scenario: Missing audio file
- **WHEN** a user supplies a path that does not identify a readable file
- **THEN** the command SHALL exit with a non-zero status and explain the input error on standard error

### Requirement: Preserve machine-readable transcript output
The system SHALL reserve standard output for the transcript and write progress or diagnostic information to standard error.

#### Scenario: Transcript used in a pipeline
- **WHEN** a user redirects standard output from a successful transcription command
- **THEN** the redirected output SHALL contain the transcript without status banners or diagnostic messages

## REMOVED Requirements

### Requirement: Default to local model files
**Reason**: The Whisper CLI and model are already host-local; Hugging Face cache behavior no longer applies.
**Migration**: Use `transcribe-whisper`; no download option is needed.
