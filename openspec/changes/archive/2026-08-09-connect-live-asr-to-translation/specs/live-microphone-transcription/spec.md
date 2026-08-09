## MODIFIED Requirements

### Requirement: Run continuous microphone transcription
The system SHALL provide a `transcribe-microphone` command that captures audio continuously from the default system microphone, transcribes queued overlapping windows locally with Whisper, and continues until interrupted. By default it SHALL print completed transcript text for successive Whisper windows. With `--output-format ndjson`, it SHALL emit one finalized English JSON event per non-empty completed transcript on standard output and write the readable English transcript to standard error.

#### Scenario: Start live transcription
- **WHEN** a user runs `uv run transcribe-microphone` with microphone permission and a usable Whisper installation
- **THEN** the command SHALL remain active, continuously capture microphone audio, and print completed transcript text for successive Whisper windows

#### Scenario: Ongoing transcription output
- **WHEN** the command processes successive microphone windows
- **THEN** it SHALL NOT print a recurring Whisper model-status line between transcript lines

#### Scenario: Structured transcript output
- **WHEN** a user runs `uv run transcribe-microphone --output-format ndjson` and a non-empty finalized transcript is available
- **THEN** standard output SHALL contain one valid JSON event with `id`, `text`, `start_ms`, and `end_ms`, and the readable English text SHALL be written to standard error

#### Scenario: Stop live transcription
- **WHEN** the user presses Ctrl-C while the command is active
- **THEN** the command SHALL stop capture, terminate active Whisper work, clean up temporary audio resources, and exit without a traceback
