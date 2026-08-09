# live-microphone-transcription Specification

## Purpose
TBD - created by archiving change add-live-microphone-transcription. Update Purpose after archive.
## Requirements
### Requirement: Run continuous microphone transcription
The system SHALL provide a `transcribe-microphone` command that captures audio continuously from the default system microphone, transcribes queued audio locally with Whisper, and continues until interrupted. By default it SHALL use fixed 5-second windows beginning every 4 seconds and print completed transcript text for successive Whisper windows. With `--segmentation vad`, it SHALL use local pause-delimited phrase audio instead. With `--output-format ndjson`, it SHALL emit one finalized English JSON event per non-empty completed transcript on standard output and write the readable English transcript to standard error.

#### Scenario: Start fixed-window live transcription
- **WHEN** a user runs `uv run transcribe-microphone` with microphone permission and a usable Whisper installation
- **THEN** the command SHALL remain active, continuously capture microphone audio, use fixed 5-second windows beginning every 4 seconds, and print completed transcript text for successive Whisper windows

#### Scenario: Start VAD live transcription
- **WHEN** a user runs `uv run transcribe-microphone --segmentation vad` with microphone permission, a usable local VAD installation, and a usable Whisper installation
- **THEN** the command SHALL continuously capture microphone audio and send pause-delimited bounded phrases to Whisper

#### Scenario: Ongoing transcription output
- **WHEN** the command processes successive microphone windows or VAD phrases
- **THEN** it SHALL NOT print a recurring Whisper model-status line between transcript lines

#### Scenario: Structured transcript output
- **WHEN** a user runs `uv run transcribe-microphone --output-format ndjson` and a non-empty finalized transcript is available
- **THEN** standard output SHALL contain one valid JSON event with `id`, `text`, `start_ms`, and `end_ms`, and the readable English text SHALL be written to standard error

#### Scenario: Stop live transcription
- **WHEN** the user presses Ctrl-C while the command is active
- **THEN** the command SHALL stop capture, terminate active Whisper work, clean up temporary audio resources, and exit without a traceback

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

