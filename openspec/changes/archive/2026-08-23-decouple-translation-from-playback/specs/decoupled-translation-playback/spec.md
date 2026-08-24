## ADDED Requirements

### Requirement: Decouple translation availability from Spanish audio playback
The browser demo SHALL process completed phrases through a translation stage and a separate Spanish-audio playback stage. After a phrase translation completes, the system SHALL publish the completed Spanish text to the browser and enqueue a correlated Spanish speech job without waiting for Piper synthesis or output playback of an earlier job. The system SHALL retain `phrase_id` and `source_segment_ids` through both stages.

#### Scenario: Publish Spanish while prior audio is playing
- **WHEN** Piper is synthesizing or playing an earlier Spanish phrase and a later phrase translation completes
- **THEN** the browser SHALL receive the later completed Spanish translation without waiting for the earlier audio to complete
- **AND** the later speech job SHALL be eligible for the ordered playback queue

### Requirement: Keep Spanish playback ordered and bounded
The system SHALL use one finite in-memory queue for unstarted Spanish speech jobs and one playback worker that invokes Piper/output for no more than one job at a time. It SHALL play admitted jobs in FIFO order. The queue capacity SHALL be documented and configurable for the demo.

#### Scenario: Play admitted jobs in order
- **WHEN** multiple Spanish speech jobs are admitted while playback is active
- **THEN** the system SHALL start each admitted job only after the preceding admitted job finishes or fails

#### Scenario: Protect live translation from audio overload
- **WHEN** a translated Spanish speech job arrives while the unstarted playback queue is at capacity
- **THEN** the system SHALL evict the oldest unstarted job, record it as skipped, admit the newest job, and continue publishing completed Spanish translations to the browser
- **AND** the system SHALL NOT interrupt an already-playing phrase

### Requirement: Make playback backlog explicit
The system SHALL report an operator-visible audio-backlog condition whenever an unstarted Spanish speech job is skipped. It SHALL record speech-job enqueue, dequeue, playback start/completion, queue item count, oldest queued-job age, and skipped-job reason in the local timing trace. It SHALL distinguish a translated-but-audio-skipped segment from a translation or playback failure.

#### Scenario: Trace an audio skip
- **WHEN** the playback queue evicts an unstarted job because it is full
- **THEN** the timing trace SHALL retain the job's phrase and source-segment lineage, queue observations, skip reason, and a terminal audio-skipped state

#### Scenario: Recover after overload
- **WHEN** the playback queue has drained after an audio-backlog condition
- **THEN** the operator-facing status SHALL return to normal while subsequent admitted jobs continue in FIFO order
