## MODIFIED Requirements

### Requirement: Replay a local WAV through the selected VAD evaluation path

The repository SHALL provide a developer-only recorded-VAD evaluator that accepts a readable 16 kHz mono WAV file, uses source-relative timestamps, and evaluates exactly one selected local backend: `webrtc` or `silero`. It SHALL not open a microphone or audio-output device. Its selected backend behavior SHALL mirror the corresponding live phrase-segmentation path.

#### Scenario: Evaluate the WebRTC baseline

- **WHEN** a developer runs the evaluator with `--vad-backend webrtc` and a valid WAV
- **THEN** it SHALL replay the WAV through the existing Python/WebRTC pause-segmentation behavior and transcribe each emitted phrase locally

#### Scenario: Evaluate the stateful Silero alternative

- **WHEN** a developer runs the evaluator with `--vad-backend silero` and compatible local Silero runtime and model assets are available
- **THEN** it SHALL replay source audio through the continuous local Silero phrase-segmentation behavior
- **AND** SHALL transcribe each finalized phrase once without overlapping-window Whisper transcript reconciliation

#### Scenario: Reject incompatible input before evaluation

- **WHEN** the supplied audio is missing or is not a 16 kHz mono WAV
- **THEN** the evaluator SHALL exit unsuccessfully before transcription and identify the required input format

### Requirement: Produce durable, comparable evaluation artifacts

The evaluator SHALL write one NDJSON transcript artifact for its selected backend. Every non-empty result line SHALL contain `id`, `start_ms`, `end_ms`, and `text`, with offsets relative to the supplied WAV. It SHALL also write a run manifest that identifies the selected backend, audio input, local Whisper and VAD model/runtime paths where applicable, and effective evaluation options.

#### Scenario: Inspect a successful backend run

- **WHEN** an evaluation completes successfully
- **THEN** its output directory SHALL contain the backend's timestamped NDJSON transcript and a manifest sufficient to identify how it was produced

#### Scenario: Preserve previous results

- **WHEN** an output artifact path already exists and overwrite was not explicitly requested
- **THEN** the evaluator SHALL fail without replacing the existing artifact
