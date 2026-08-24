# runtime-vad-backend-selection Specification

## Purpose

Select a local VAD implementation for live microphone transcription.

## Requirements

### Requirement: Runtime VAD backend selection

The system SHALL provide a runtime selector for the VAD backend used by VAD-segmented local microphone transcription. It SHALL offer `webrtc` as the default baseline backend and `silero` as a continuous, stateful local speech-segmentation alternative, and SHALL report the selected backend when a run starts. Both backends SHALL emit finalized phrase events into the same downstream local Whisper, translation, TTS, and display pipeline.

#### Scenario: Use the default backend

- **WHEN** a user runs VAD-segmented microphone transcription without a VAD-backend option
- **THEN** the system uses the existing local WebRTC backend
- **AND** reports that `webrtc` is selected

#### Scenario: Select stateful Silero VAD

- **WHEN** a user runs VAD-segmented microphone transcription with the Silero backend selected and compatible local Silero support is available
- **THEN** the system uses the continuous local Silero phrase-segmentation path
- **AND** reports that `silero` is selected

#### Scenario: Keep backend choice within one pipeline

- **WHEN** either supported VAD backend finalizes a phrase
- **THEN** the system SHALL send that phrase through the same local Whisper and downstream pipeline
- **AND** SHALL emit the existing finalized transcript event shape

### Requirement: Early Silero capability validation

The system SHALL validate the installed local Silero runtime and required local Silero model asset before opening the microphone for a Silero-backed run. It SHALL fail with an actionable error when that support is unavailable and SHALL identify WebRTC as the available baseline backend.

#### Scenario: Stateful Silero support is unavailable

- **WHEN** a user selects the Silero backend but the installed local Silero runtime or required local asset is unavailable
- **THEN** the command exits before microphone capture begins
- **AND** standard error explains the unavailable prerequisite and how to select the WebRTC backend
