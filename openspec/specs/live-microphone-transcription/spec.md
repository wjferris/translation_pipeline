# live-microphone-transcription Specification

## Purpose
TBD - created by archiving change add-live-microphone-transcription. Update Purpose after archive.
## Requirements
### Requirement: Run continuous microphone transcription
The system SHALL provide a `transcribe-microphone` command that captures audio continuously from the default system microphone, transcribes queued audio locally with Whisper, and continues until interrupted. By default it SHALL use fixed 5-second windows beginning every 4 seconds and print completed transcript text for successive Whisper windows. With `--segmentation vad`, it SHALL use local pause-delimited phrase audio using the selected local VAD backend, defaulting to WebRTC. With `--output-format ndjson`, it SHALL emit one finalized English JSON event per non-empty completed transcript on standard output and write the readable English transcript to standard error.

#### Scenario: Start fixed-window live transcription
- **WHEN** a user runs `uv run transcribe-microphone` with microphone permission and a usable Whisper installation
- **THEN** the command SHALL remain active, continuously capture microphone audio, use fixed 5-second windows beginning every 4 seconds, and print completed transcript text for successive Whisper windows

#### Scenario: Start VAD live transcription
- **WHEN** a user runs `uv run transcribe-microphone --segmentation vad` with microphone permission, a usable local VAD installation, and a usable Whisper installation
- **THEN** the command SHALL continuously capture microphone audio and send pause-delimited bounded phrases to Whisper

#### Scenario: Start Silero-backed VAD live transcription
- **WHEN** a user runs `uv run transcribe-microphone --segmentation vad --vad-backend silero` with compatible local Whisper/Silero support
- **THEN** the command SHALL continuously capture microphone audio and use the local Silero-backed VAD path for finalized transcription events

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

### Requirement: Configure local microphone input gain
The system SHALL allow `transcribe-microphone` callers to set `--input-gain-db` as a floating-point gain from -48 dB through +48 dB, inclusive. The option SHALL default to `0 dB`. Before the system queues each captured normalized microphone block for fixed-window or VAD segmentation, it SHALL multiply the block by the linear factor `10 ** (input_gain_db / 20)` and clip every output sample to the inclusive range `[-1.0, 1.0]`. The system SHALL write the selected input gain to standard error in its startup status.

#### Scenario: Use the default zero-gain capture path
- **WHEN** a user starts `transcribe-microphone` without `--input-gain-db`
- **THEN** the system SHALL queue the captured samples unchanged by gain multiplication and report `0 dB` input gain at startup

#### Scenario: Amplify a quiet line input
- **WHEN** a user starts `transcribe-microphone --input-gain-db 30`
- **THEN** the system SHALL multiply every captured sample by the linear factor for +30 dB before fixed-window or VAD segmentation and report `+30 dB` input gain at startup

#### Scenario: Prevent amplified samples from exceeding the audio range
- **WHEN** a configured gain would produce a sample greater than `1.0` or less than `-1.0`
- **THEN** the system SHALL queue that sample as `1.0` or `-1.0`, respectively

#### Scenario: Reject an unsupported input gain
- **WHEN** a user supplies `--input-gain-db` outside -48 dB through +48 dB
- **THEN** the command SHALL exit with status 2 before opening the microphone and write an actionable validation error to standard error
