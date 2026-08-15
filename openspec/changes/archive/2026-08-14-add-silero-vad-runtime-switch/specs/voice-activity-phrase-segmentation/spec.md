## MODIFIED Requirements

### Requirement: Segment continuous audio on local voice activity
The system SHALL provide a local VAD segmentation mode that converts continuous 16 kHz mono microphone audio into bounded phrase audio for local Whisper transcription without uploading audio. It SHALL support the selected local VAD backend while retaining WebRTC as the default backend.

#### Scenario: Release a phrase after speech pause
- **WHEN** VAD has detected speech and then detects silence for the configured phrase-end duration
- **THEN** the system SHALL enqueue one phrase audio segment for Whisper transcription

#### Scenario: Bound a continuously spoken phrase
- **WHEN** detected speech continues beyond the configured maximum phrase duration
- **THEN** the system SHALL enqueue a bounded phrase segment and continue capturing later audio

#### Scenario: Preserve leading speech
- **WHEN** speech begins after a period of silence
- **THEN** the emitted phrase SHALL include the configured short pre-roll preceding detected speech

#### Scenario: Use the selected backend
- **WHEN** a user selects a supported VAD backend for VAD segmentation
- **THEN** the system SHALL apply that backend to the local phrase-detection path
- **AND** SHALL retain the existing WebRTC behavior when no backend is selected

### Requirement: Keep VAD phrase segmentation configurable and local
The system SHALL expose VAD aggressiveness, phrase-end silence, and maximum phrase-duration settings for the WebRTC backend, SHALL expose a backend selector for supported local implementations, and SHALL run the selected VAD detector locally.

#### Scenario: Tune phrase boundaries
- **WHEN** a user supplies supported VAD segmentation options
- **THEN** the command SHALL apply those values to subsequent phrase segmentation and report invalid values before opening the microphone

#### Scenario: Select a backend with incompatible tuning
- **WHEN** a user supplies a backend-specific option that is not supported by the selected VAD backend
- **THEN** the command SHALL report the incompatible option before opening the microphone
