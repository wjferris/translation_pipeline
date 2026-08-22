# recorded-vad-evaluation Specification

## Purpose
TBD - created by archiving change add-recorded-vad-evaluation. Update Purpose after archive.
## Requirements
### Requirement: Replay a local WAV through the selected VAD evaluation path
The repository SHALL provide a developer-only recorded-VAD evaluator that
accepts a readable 16 kHz mono WAV file, uses source-relative timestamps, and
evaluates exactly one selected local backend: `webrtc` or `silero`. It SHALL
not open a microphone or audio-output device.

#### Scenario: Evaluate the WebRTC baseline
- **WHEN** a developer runs the evaluator with `--vad-backend webrtc` and a valid WAV
- **THEN** it SHALL replay the WAV through the existing Python/WebRTC
  pause-segmentation behavior and transcribe each emitted phrase locally

#### Scenario: Evaluate the Silero alternative
- **WHEN** a developer runs the evaluator with `--vad-backend silero` and compatible local Whisper and Silero assets are available
- **THEN** it SHALL process source windows with Whisper-integrated Silero VAD
  and retain only transcript content not already covered by an overlapping
  preceding source window

#### Scenario: Reject incompatible input before evaluation
- **WHEN** the supplied audio is missing or is not a 16 kHz mono WAV
- **THEN** the evaluator SHALL exit unsuccessfully before transcription and
  identify the required input format

### Requirement: Produce durable, comparable evaluation artifacts
The evaluator SHALL write one NDJSON transcript artifact for its selected
backend. Every non-empty result line SHALL contain `id`, `start_ms`, `end_ms`,
and `text`, with offsets relative to the supplied WAV. It SHALL also write a
run manifest that identifies the selected backend, audio input, local model
paths, and effective evaluation options.

#### Scenario: Inspect a successful backend run
- **WHEN** an evaluation completes successfully
- **THEN** its output directory SHALL contain the backend's timestamped NDJSON
  transcript and a manifest sufficient to identify how it was produced

#### Scenario: Preserve previous results
- **WHEN** an output artifact path already exists and overwrite was not explicitly requested
- **THEN** the evaluator SHALL fail without replacing the existing artifact

### Requirement: Compare recognized text with an English subtitle reference
The developer flow SHALL accept an English SRT reference and generate a
readable comparison report for the selected backend. The report SHALL include
source timing, the reference text, the recognized text, and a clearly labeled
approximate normalized-text comparison summary.

#### Scenario: Generate a backend comparison report
- **WHEN** a valid SRT reference is supplied with a completed backend evaluation
- **THEN** the flow SHALL write a report that permits a developer to compare
  the recognized transcript with the reference over the same source timeline

#### Scenario: Run both backends against one fixture
- **WHEN** a developer uses the documented comparison flow with the same WAV
  and SRT inputs
- **THEN** it SHALL create separate artifacts and reports for `webrtc` and
  `silero` without mixing their transcript output

### Requirement: Keep recorded evaluation outside the live application surface
The recorded-VAD evaluator SHALL be exposed only through a developer runtime
script or equivalent test scaffold. It SHALL not alter the default
`transcribe-microphone`, demo, translation, or TTS commands.

#### Scenario: Run the standard live microphone command
- **WHEN** a user runs the existing live microphone command without the recorded-evaluation script
- **THEN** its supported arguments and production behavior SHALL remain unchanged

