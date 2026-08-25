## ADDED Requirements

### Requirement: Condition local Whisper with bounded prior English context
The system SHALL retain a bounded history of finalized, emitted English ASR
segments during one `transcribe-microphone` session and SHALL supply the
selected recent history to each later local Whisper invocation as decoder
context. The current segment's audio SHALL remain the source of its transcript,
and prior context SHALL NOT be emitted as part of a new event unless Whisper
recognizes corresponding current audio.

#### Scenario: Transcribe a later finalized segment with context
- **WHEN** a prior English ASR segment has been finalized and emitted and the
  next microphone segment is sent to Whisper with context enabled
- **THEN** the system SHALL pass the bounded prior English text to Whisper as
  decoder context before transcribing the current audio segment

#### Scenario: Start a fresh session
- **WHEN** `transcribe-microphone` starts a new process
- **THEN** the system SHALL begin with an empty prior-English context history
  and SHALL transcribe its first segment without preceding transcript context

#### Scenario: Disable Whisper phrase context
- **WHEN** an operator sets the Whisper context length to `0`
- **THEN** the system SHALL not supply prior English phrase text to Whisper and
  SHALL otherwise preserve the existing transcription behavior

#### Scenario: Exclude discarded transcript text
- **WHEN** a Whisper result is removed by overlap reconciliation, rejected as a
  non-speech cue, or not emitted as a finalized English segment
- **THEN** the system SHALL not add that text to the prior-English context
  history
