## ADDED Requirements

### Requirement: Transcribe a local audio file
The system SHALL provide a `transcribe-voxtral` command that accepts exactly one path to a local audio file and produces an English Voxtral transcription.

#### Scenario: Successful transcription
- **WHEN** a user runs `uv run transcribe-voxtral path/to/english-audio.wav` with a readable supported audio file
- **THEN** the command SHALL print the resulting English transcript to standard output and exit successfully

#### Scenario: Missing audio file
- **WHEN** a user supplies a path that does not identify a readable file
- **THEN** the command SHALL exit with a non-zero status and explain the input error on standard error

### Requirement: Preserve machine-readable transcript output
The system SHALL reserve standard output for the transcript and write progress or hardware-selection information to standard error.

#### Scenario: Transcript used in a pipeline
- **WHEN** a user redirects standard output from a successful transcription command
- **THEN** the redirected output SHALL contain the transcript without status banners or diagnostic messages

### Requirement: Provide a repeatable example input
The system SHALL include a public audio sample lasting between five and ten seconds that can be passed directly to the transcription command.

#### Scenario: First local experiment
- **WHEN** a user runs the documented command with the bundled sample audio
- **THEN** the command SHALL receive a readable local MP3 input without requiring the user to provide a separate recording

### Requirement: Default to local model files
The system SHALL load Voxtral model and processor files from the local Hugging Face cache by default and SHALL NOT make a Hub request during normal transcription.

#### Scenario: Cached model transcription
- **WHEN** the required Voxtral files are present in the local cache and a user runs the transcription command without download options
- **THEN** the command SHALL load the files locally and transcribe without contacting Hugging Face

#### Scenario: Intentional model download
- **WHEN** a user needs to obtain or refresh Voxtral files and runs the command with `--download`
- **THEN** the command SHALL allow Hugging Face access for that invocation

#### Scenario: Missing cached model files
- **WHEN** a user runs the command without `--download` and required Voxtral files are absent locally
- **THEN** the command SHALL exit with a non-zero status and instruct the user to rerun with `--download`
