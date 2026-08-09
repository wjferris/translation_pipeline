# overlapped-live-transcription Specification

## Purpose
TBD - created by archiving change add-overlapped-live-transcription. Update Purpose after archive.
## Requirements
### Requirement: Capture audio without transcription gaps
The system SHALL capture default-microphone audio continuously while local Whisper transcribes earlier audio windows.

#### Scenario: Whisper processes a prior window
- **WHEN** Whisper is transcribing one queued audio window
- **THEN** the microphone capture component SHALL continue collecting later audio without waiting for Whisper to complete

### Requirement: Use overlapping transcription windows
The system SHALL create transcription windows with a configurable overlap. Its initial default SHALL use a six-second window and a five-second stride.

#### Scenario: Speech crosses a window boundary
- **WHEN** a spoken phrase spans the five-second stride boundary
- **THEN** the relevant boundary audio SHALL be present in both adjacent Whisper windows

### Requirement: De-duplicate overlap transcript text
The system SHALL attempt conservative word-level removal of duplicated text caused by overlapping windows before writing new live transcript output.

#### Scenario: Matching overlap text
- **WHEN** the end of one displayed transcript and the beginning of the next transcript contain matching normalized words
- **THEN** the system SHALL print the matching words once

### Requirement: Report transcription backlog
The system SHALL emit a standard-error warning when queued windows indicate that transcription is falling behind capture.

#### Scenario: Worker slower than capture
- **WHEN** queued windows exceed the configured warning threshold
- **THEN** the command SHALL report that live transcription is behind

