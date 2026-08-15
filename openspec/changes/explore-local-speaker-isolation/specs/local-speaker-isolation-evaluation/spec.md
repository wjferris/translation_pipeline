## ADDED Requirements

### Requirement: Evaluate local pre-ASR speaker isolation

The project SHALL evaluate any candidate speaker-isolation or noise-suppression
stage against the unprocessed direct podium feed before integrating it into the
live translation pipeline. The evaluation SHALL use local processing and SHALL
record speech preservation, suppression behavior, latency, routing
compatibility, and operational stability.

#### Scenario: Compare a candidate with the direct feed

- **WHEN** a candidate pre-ASR enhancement path is evaluated
- **THEN** it SHALL be tested with the same podium speech, competing audience
  speech, and transient-noise material as the direct-feed baseline
- **AND** the resulting observations SHALL be recorded with a recommend,
  defer, or reject decision

#### Scenario: Reject incompatible processing

- **WHEN** a candidate requires cloud audio processing, cannot expose a stable
  selectable macOS input for the local capture path, or degrades desired speech
  or acceptable latency
- **THEN** it SHALL be rejected for the live POC
- **AND** the unprocessed direct feed SHALL remain available as the fallback

### Requirement: Preserve reversible live-audio routing

The project SHALL not make a candidate enhancement stage the required live
audio path until it has passed the evaluation. Any later adopted route SHALL
retain a documented direct-feed fallback.

#### Scenario: Recover from an enhancement failure

- **WHEN** an evaluated or later integrated enhancement route fails during
  setup or live use
- **THEN** the operator SHALL be able to select the documented direct input
  route without changing the translation, VAD, or output stages
