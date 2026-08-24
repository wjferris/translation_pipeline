## MODIFIED Requirements

### Requirement: Record high-resolution stage and queue timing
The system SHALL record all reached timing boundaries as session-relative monotonic nanoseconds and SHALL use a `timestamps_ns` object containing these fields: `source_audio_start`, `source_audio_end`, `vad_detected_start`, `vad_segment_closed`, `asr_start`, `asr_complete`, `translation_start`, `translation_complete`, `tts_start`, `tts_first_audio`, `tts_complete`, `playback_start`, and `playback_complete`. It SHALL record phrase-buffer boundaries when needed to calculate waiting time. A boundary not reached or unavailable in the selected mode SHALL be `null`.

For every measurable queue, the system SHALL record the depth when the segment enters and leaves the stage. For an unobservable operating-system pipe or handoff, it SHALL record physical queue depth as `null` and SHALL record a logical pending count only when it can be calculated without estimation. For the demo's Spanish speech-job queue, it SHALL record enqueue/dequeue item count, oldest queued-job age, and an explicit skip observation when an unstarted job is evicted for capacity.

#### Scenario: Record ASR timing and queue depth
- **WHEN** a segment enters and leaves the ASR work queue and ASR completes
- **THEN** the trace SHALL contain its ASR enqueue/dequeue depth, `asr_start`, and `asr_complete` values on the shared monotonic timeline

#### Scenario: A downstream pipe has no observable physical depth
- **WHEN** a segment waits in a subprocess pipe whose physical queue depth cannot be read reliably
- **THEN** the trace SHALL represent physical queue depth as `null` and retain the available adjacent stage timestamps for later wait-time analysis

#### Scenario: Record bounded Spanish playback queue activity
- **WHEN** a translated phrase enters, leaves, or is evicted from the Spanish speech-job queue
- **THEN** the trace SHALL retain its phrase/source-segment lineage, logical item count, oldest queued-job age when applicable, and the relevant enqueue, dequeue, or skip lifecycle event
