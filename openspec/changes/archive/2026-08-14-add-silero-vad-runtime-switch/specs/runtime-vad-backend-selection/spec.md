## ADDED Requirements

### Requirement: Runtime VAD backend selection
The system SHALL provide a runtime selector for the VAD backend used by VAD-segmented local microphone transcription. It SHALL offer `webrtc` as the default baseline backend and `silero` as the integrated-local-Whisper alternative, and SHALL report the selected backend when a run starts.

#### Scenario: Use the default backend
- **WHEN** a user runs VAD-segmented microphone transcription without a VAD-backend option
- **THEN** the system uses the existing local WebRTC backend
- **AND** reports that `webrtc` is selected

#### Scenario: Select integrated Silero VAD
- **WHEN** a user runs VAD-segmented microphone transcription with the Silero backend selected and compatible local Whisper support is available
- **THEN** the system uses the local Whisper-integrated Silero VAD path
- **AND** reports that `silero` is selected

#### Scenario: Reconcile overlapping Silero capture windows
- **WHEN** successive Silero capture windows overlap
- **THEN** the system SHALL use Whisper's local JSON timing offsets to suppress
  transcript segments fully covered by the preceding window
- **AND** SHALL retain the timestamps of segments that extend into newly
  captured audio

### Requirement: Early Silero capability validation
The system SHALL validate the installed local Whisper executable and any required local Silero VAD asset before opening the microphone for a Silero-backed run. It SHALL fail with an actionable error when that support is unavailable and SHALL identify WebRTC as the available baseline backend.

#### Scenario: Integrated Silero support is unavailable
- **WHEN** a user selects the Silero backend but the installed local Whisper executable or required local asset does not support it
- **THEN** the command exits before microphone capture begins
- **AND** standard error explains the unavailable prerequisite and how to select the WebRTC backend
