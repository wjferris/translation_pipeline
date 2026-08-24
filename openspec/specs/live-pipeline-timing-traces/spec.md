# live-pipeline-timing-traces Specification

## Purpose

Provide local, high-resolution per-segment instrumentation that measures and attributes live translation latency without changing pipeline behavior.

## Requirements

### Requirement: Create an identifiable private timing-trace run
The system SHALL create a unique owner-private trace directory before starting each browser-demo run unless the operator explicitly passes `--no-timing-trace` for a controlled baseline. It SHALL create the directory beneath `/tmp/babelfish-live-runs/` using the identifier `YYYY_MM_DD_NNN`, where `YYYY_MM_DD` is the local date and `NNN` is a zero-padded per-date sequence. The system SHALL create `manifest.json`, report the directory path to standard error, and record the run configuration, wall-clock label, monotonic timebase, trace schema version, and final completion state.

#### Scenario: Allocate distinct runs on one day
- **WHEN** two browser demos start on the same local date
- **THEN** the system SHALL create two distinct unused directories matching `YYYY_MM_DD_NNN` without overwriting either run

#### Scenario: Trace setup is unavailable
- **WHEN** the system cannot create the private trace directory or initial manifest
- **THEN** the demo SHALL exit before microphone capture begins and report an actionable trace-setup error to standard error

#### Scenario: Run an untraced comparison baseline
- **WHEN** an operator starts the demo with `--no-timing-trace`
- **THEN** the system SHALL run the same selected pipeline configuration without creating a trace directory or exporting trace metadata to workers

### Requirement: Correlate every source segment through the pipeline
The system SHALL assign a unique `segment_id` to each bounded source-audio segment before ASR. It SHALL record `source_audio_start` and `source_audio_end` for every segment. In VAD mode, it SHALL also record `vad_detected_start` and `vad_segment_closed`; in a mode without VAD, those fields SHALL be `null`. When phrase buffering combines source segments, the system SHALL assign a `phrase_id` and retain every contributing `segment_id` in `source_segment_ids`. Translation, TTS, and playback records SHALL retain that phrase identity and source-segment lineage.

#### Scenario: Trace a VAD utterance
- **WHEN** VAD detects and closes a source utterance that is sent to ASR
- **THEN** the trace SHALL contain one unique `segment_id` with source-audio and VAD boundary timestamps before ASR timing is recorded

#### Scenario: Trace a phrase built from multiple source segments
- **WHEN** the phrase buffer emits one phrase from multiple ASR segments
- **THEN** the phrase, translation, TTS, and playback trace records SHALL retain one `phrase_id` and the complete `source_segment_ids` list

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

### Requirement: Persist complete outputs and derived per-segment latency metrics
The system SHALL write complete enriched text events to `asr.ndjson`, `phrases.ndjson`, `translations.ndjson`, and `playback.ndjson`, and append stage lifecycle records to `timing.ndjson`. It SHALL write one terminal record per `segment_id` to `segments.ndjson` containing all available timestamps, source-audio duration, queue observations, completion state, and these derived metrics when their operands are available:

- VAD duration
- ASR processing duration
- Translation processing duration
- TTS processing duration
- Time to first TTS audio
- Playback duration
- Queue/wait time before each stage
- End-to-end latency from `source_audio_end` to `playback_start`
- End-to-end completion latency from `source_audio_end` to `playback_complete`
- ASR and TTS real-time factor, calculated as `processing_time / source_audio_duration`

#### Scenario: Complete playback for a segment
- **WHEN** Piper finishes playing a translated phrase containing a source segment
- **THEN** that segment's terminal metric record SHALL contain the available derived values, including source-to-playback start/completion latency and ASR/TTS RTF when source duration is non-zero

#### Scenario: End a run before playback completes
- **WHEN** the operator interrupts a demo before a segment reaches a terminal downstream stage
- **THEN** the system SHALL preserve existing NDJSON evidence and write an interrupted or incomplete segment record with unreached timestamps and metrics as `null`

### Requirement: Support backlog attribution and later visual analysis
The persisted data SHALL support an end-to-end latency-over-session plot whose x-axis is source audio/session time and whose y-axis is each segment's age at `playback_start`. It SHALL also support a per-segment latency breakdown of VAD, ASR, translation, TTS, playback, and queue/wait time. The data SHALL make it possible to distinguish stable expected latency, short-term jitter, a specific slow stage, queue growth, and sustained cumulative delay indicated by a positive latency slope over source time.

#### Scenario: Detect sustained cumulative delay
- **WHEN** successive terminal segment records show increasing source-to-playback-start latency over their source timeline
- **THEN** the trace SHALL provide the timestamps, derived wait times, RTF values, and queue observations needed to attribute the growth to one or more stages

### Requirement: Minimize instrumentation impact on live processing
The system SHALL collect trace records only at source-segment, VAD, stage-entry, stage-completion, and playback boundaries; it SHALL NOT write trace files or emit a trace record for every PCM callback block or audio frame. The live processing path SHALL capture only directly available identifiers, counters, and a monotonic timestamp, then submit the record to one bounded non-blocking in-memory trace queue. A background writer SHALL serialize and batch local NDJSON output without forcing a per-record durable flush or `fsync`.

If the trace queue is full, the system SHALL NOT block live capture, ASR, translation, TTS, or playback. It SHALL mark the trace incomplete, record a diagnostic-overflow count in the manifest when possible, and continue the live pipeline. Metric assembly and normal-shutdown trace draining SHALL occur outside the audio callback and stage hot paths.

#### Scenario: Record a VAD boundary without blocking audio capture
- **WHEN** VAD detects speech or closes a source segment
- **THEN** the system SHALL enqueue its minimal timing record without performing trace file I/O from the audio callback or VAD processing path

#### Scenario: Trace writer cannot keep up
- **WHEN** the bounded trace queue reaches capacity during a live run
- **THEN** the system SHALL retain live processing behavior, mark the trace incomplete, and record that diagnostic events were discarded rather than waiting for trace capacity

### Requirement: Keep instrumentation local and observational
The system SHALL not upload trace data or raw captured audio. It SHALL not change model selection, stage order, playback order, queue policy, or retry behavior solely to collect instrumentation. If a trace write fails after startup, the system SHALL report the failure to standard error, mark the manifest incomplete when possible, and continue live processing.

#### Scenario: Trace write fails during a live demo
- **WHEN** a trace file becomes unwritable after workers have started
- **THEN** the system SHALL report the diagnostic failure and continue the local live pipeline without a cloud fallback or automatic performance change
