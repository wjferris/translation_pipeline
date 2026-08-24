## Context

The live browser demo receives continuously captured audio, forms VAD-bounded segments, transcribes them, joins ASR events into translation phrases, translates locally, and synthesizes/plays Spanish sequentially. A growing end-of-discourse lag suggests that one or more stages cannot keep pace, but the current event flow records neither stage start/end times nor downstream queueing.

## Goals / Non-Goals

**Goals:**

- Make every traced audio segment attributable across VAD, ASR, phrase buffering, translation, TTS, and playback.
- Record all available stage boundaries with one shared, high-resolution monotonic timebase.
- Persist complete stage output and derived metrics sufficient to identify fixed latency, jitter, queue growth, a slow stage, and sustained backlog.
- Create one collision-safe, owner-private, identifiable `/tmp` directory per demo run.
- Preserve useful partial evidence when a run is interrupted.
- Keep the instrumentation itself from becoming a meaningful source of queueing or latency.

**Non-Goals:**

- Change model selection, VAD settings, queue policy, stage ordering, retry behavior, or audio routing.
- Automatically compensate for, drop, or optimize latency.
- Record raw captured audio, send telemetry off the machine, or provide an interactive visualization UI in this change.

## Decisions

### Use source segments as the primary correlation unit

The microphone/VAD boundary will allocate a unique `segment_id` for each bounded source-audio utterance; fixed-window mode will allocate the ID when its audio window closes. Each segment carries `source_audio_start` and `source_audio_end`, and VAD mode additionally records `vad_detected_start` and `vad_segment_closed`.

Phrase buffering can combine multiple source segments. It will therefore allocate a `phrase_id` and retain `source_segment_ids`. Translation, TTS, and playback timing is recorded against that phrase and copied into the terminal metric record for every contributing `segment_id`. This preserves a per-source-segment latency series while making shared downstream work explicit.

Using only the existing ASR IDs was considered, but it cannot time VAD detection or distinguish a source segment from a later multi-segment phrase.

### Use a session-relative monotonic nanosecond timeline

The coordinator creates a `timebase_monotonic_ns` at run start and passes it to child workers. All latency timestamps are stored as non-negative, session-relative integer nanoseconds in a `timestamps_ns` object. The object uses these exact boundary names whenever the boundary is reached:

- `source_audio_start`, `source_audio_end`
- `vad_detected_start`, `vad_segment_closed`
- `asr_start`, `asr_complete`
- `translation_start`, `translation_complete`
- `tts_start`, `tts_first_audio`, `tts_complete`
- `playback_start`, `playback_complete`

Additional phrase-buffer boundaries may be recorded to calculate its own wait time. A boundary unavailable for a mode or interrupted run is represented as `null`, never fabricated. The manifest may include wall-clock start/end labels solely for operator correlation; elapsed-time calculations use only the monotonic timeline.

`time.monotonic_ns()` is chosen over wall-clock time because wall-clock changes can corrupt duration calculations. Milliseconds-only storage was rejected because short VAD, callback, and TTS-first-audio intervals need higher resolution.

### Persist complete stage events, lifecycle events, and terminal segment metrics

Each run directory contains the following owner-private files:

- `manifest.json`: schema version, run ID, wall-clock labels, timebase, configuration, file layout, and completion status.
- `asr.ndjson`, `phrases.ndjson`, `translations.ndjson`, and `playback.ndjson`: complete text events at their respective boundaries, enriched with IDs and all known timing lineage.
- `timing.ndjson`: append-only lifecycle events for every reached boundary, including `segment_id` or `phrase_id`, timestamp, and queue observations.
- `segments.ndjson`: one terminal record per `segment_id`, including all available timestamps, queue depths, derived metrics, and an explicit completion state.

Each terminal segment record derives: source-audio duration; VAD, ASR, translation, TTS, first-TTS-audio, and playback durations; wait time before every available stage; end-to-end latency from source end to playback start and completion; and ASR/TTS real-time factors. `RTF = processing_time / source_audio_duration`; ASR and TTS RTF are required whenever source duration and the respective completion boundary are available.

The complete stage files preserve the original text evidence, while `segments.ndjson` is the analysis-ready data source. CSV can be generated later; NDJSON avoids an additional dependency and accommodates missing/interrupted boundaries naturally.

### Minimize the observer effect with asynchronous, boundary-only tracing

The hot path will capture only an O(1) `time.monotonic_ns()` value, the already-known segment/phrase identifier, and a directly available queue counter at a segment or stage boundary. It will not trace individual PCM callback blocks or frames.

Those small records enter a single bounded in-memory trace queue consumed by one background writer. The writer batches local NDJSON appends and does not `fsync` or force a durable flush for each record. File I/O, serialization, metric assembly, and normal-shutdown draining occur outside the audio callback and model/playback work.

If the trace queue reaches capacity, the pipeline will not wait for it. The trace is marked incomplete, an overflow count is retained in the manifest, and later trace records may be discarded while live audio continues unchanged. This is preferable to creating the very backlog the instrument is intended to measure. A bounded queue was chosen over an unbounded queue to prevent diagnostics from consuming memory during a failure.

### Define queue depth precisely and allow unavailable observations

At a measurable in-process queue, records capture the depth when a segment is enqueued and dequeued. The ASR window queue is an example. At subprocess pipes or serial handoffs where the OS queue depth is not observable, the trace records `null` for physical depth and records a logical pending count only when it can be calculated from known stage entries and terminal exits.

Wait time remains mandatory whenever adjacent timestamps exist, even if physical queue depth is unavailable. This avoids inventing queue measurements while still showing downstream backpressure through rising wait time and logical pending count.

### Keep tracing observational and fail safely

Every `demo` invocation creates `/tmp/babelfish-live-runs/YYYY_MM_DD_NNN`, where `NNN` is a collision-safe zero-padded per-date sequence such as `001`. Failure to create the private run directory and initial manifest prevents demo startup. After startup, trace write errors are reported and mark the manifest incomplete, but do not change live processing behavior.

Tracing is enabled by default. `--no-timing-trace` is an explicit diagnostic-baseline mode that starts the otherwise unchanged demo without creating a run directory or exporting trace metadata to workers. It exists only to measure instrumentation overhead against the normal traced configuration; it does not select a different model or change stage behavior.

The first implementation records data for later visualization rather than generating charts. The schema must directly support: (1) a plot of end-to-end playback-start latency over source/session time and (2) a per-segment breakdown of VAD, ASR, translation, TTS, playback, and wait time.

## Risks / Trade-offs

- [Trace output contains spoken English and Spanish] → Use owner-only permissions, do not retain audio, and document that `/tmp` is ephemeral and requires deliberate copying for longer retention.
- [Tracing perturbs live performance] → Capture only stage-boundary timestamps/counters, use a bounded non-blocking writer queue, batch local writes, and compare a traced short run with the current baseline.
- [The writer falls behind] → Mark the trace incomplete and count discarded diagnostics rather than blocking, growing memory, or changing live processing.
- [Cross-process clocks or segment lineage disagree] → Use a shared monotonic timebase, assign IDs before ASR, and test multi-segment phrase correlation.
- [Piper synthesis and playback overlap in one loop] → Define TTS boundaries at synthesis invocation/first/last generated audio and playback boundaries at output-device start/finish; retain both rather than assuming they are identical.
- [An interrupted run has missing terminal boundaries] → Preserve prior lifecycle events and write terminal records with `null` fields plus `interrupted` or `incomplete` state.

## Migration Plan

There is no existing trace format to migrate. New runs create fresh directories below `/tmp/babelfish-live-runs/`; removing the feature later simply stops new trace creation. Existing directories can expire with the OS temporary-storage policy or be copied deliberately before cleanup.

## Open Questions

None. The initial trace schema is intentionally sufficient for offline charts; chart-generation tooling can follow after real traces establish the most useful presentation.
