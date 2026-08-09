## ADDED Requirements

### Requirement: Run continuous microphone transcription
The system SHALL provide a `transcribe-microphone` command that captures audio from the default system microphone in consecutive short chunks, transcribes each chunk locally with Whisper, and continues until interrupted.

#### Scenario: Start live transcription
- **WHEN** a user runs `uv run transcribe-microphone` with microphone permission and a usable Whisper installation
- **THEN** the command SHALL remain active and print completed transcript text for successive microphone-audio chunks

#### Scenario: Ongoing transcription output
- **WHEN** the command processes successive microphone chunks
- **THEN** it SHALL NOT print a recurring Whisper model-status line between transcript lines

#### Scenario: Stop live transcription
- **WHEN** the user presses Ctrl-C while the command is active
- **THEN** the command SHALL stop capture, clean up temporary audio resources, and exit without a traceback

### Requirement: Keep audio processing local
The system SHALL send microphone chunks only to the locally installed Whisper executable and SHALL NOT upload captured audio to a remote service.

#### Scenario: Offline microphone transcription
- **WHEN** the command transcribes a captured audio chunk
- **THEN** it SHALL use the configured local Whisper model and produce output without a network request

### Requirement: Report microphone access failures
The system SHALL provide an actionable standard-error message when the default microphone cannot be opened.

#### Scenario: Microphone permission denied
- **WHEN** macOS denies microphone access to the launching application
- **THEN** the command SHALL exit with a non-zero status and tell the user to grant microphone permission
