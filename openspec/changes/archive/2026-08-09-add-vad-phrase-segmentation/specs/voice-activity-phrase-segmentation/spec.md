## ADDED Requirements

### Requirement: Segment continuous audio on local voice activity
The system SHALL provide a local VAD segmentation mode that converts continuous 16 kHz mono microphone audio into bounded phrase audio for local Whisper transcription without uploading audio.

#### Scenario: Release a phrase after speech pause
- **WHEN** VAD has detected speech and then detects silence for the configured phrase-end duration
- **THEN** the system SHALL enqueue one phrase audio segment for Whisper transcription

#### Scenario: Bound a continuously spoken phrase
- **WHEN** detected speech continues beyond the configured maximum phrase duration
- **THEN** the system SHALL enqueue a bounded phrase segment and continue capturing later audio

#### Scenario: Preserve leading speech
- **WHEN** speech begins after a period of silence
- **THEN** the emitted phrase SHALL include the configured short pre-roll preceding detected speech

### Requirement: Keep VAD phrase segmentation configurable and local
The system SHALL expose VAD aggressiveness, phrase-end silence, and maximum phrase-duration settings, and SHALL run the VAD detector locally.

#### Scenario: Tune phrase boundaries
- **WHEN** a user supplies supported VAD segmentation options
- **THEN** the command SHALL apply those values to subsequent phrase segmentation and report invalid values before opening the microphone
