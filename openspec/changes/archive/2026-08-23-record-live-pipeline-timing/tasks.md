## 1. Trace-run foundation

- [x] 1.1 Add an owner-private, collision-safe trace-run allocator for `/tmp/babelfish-live-runs/YYYY_MM_DD_NNN` and initialize `manifest.json` before demo workers start.
- [x] 1.2 Define the versioned NDJSON schema, session-relative `monotonic_ns` timebase, wall-clock labels, completion states, and all required timing/metric fields.
- [x] 1.3 Record demo configuration in the manifest, including models, VAD settings, input gain, devices, and trace-write failures.
- [x] 1.4 Add one bounded non-blocking trace-record queue and a background batch writer; track and persist trace overflow without blocking live work.
- [x] 1.5 Add a default-off `--no-timing-trace` baseline switch that bypasses trace allocation and worker trace metadata without changing pipeline configuration.

## 2. Source, VAD, and ASR instrumentation

- [x] 2.1 Allocate `segment_id` values at the source-segmentation boundary and record source-audio start/end for fixed-window and VAD modes without per-frame or per-callback trace I/O.
- [x] 2.2 Record VAD detection/close timestamps when VAD is enabled, leaving those fields explicitly null when it is not.
- [x] 2.3 Pass the shared monotonic timebase to the microphone worker and instrument ASR enqueue/dequeue depth, ASR start, and ASR completion.
- [x] 2.4 Persist complete enriched ASR output to `asr.ndjson` and lifecycle events to `timing.ndjson`.

## 3. Downstream stage instrumentation

- [x] 3.1 Preserve segment lineage through phrase buffering, assign `phrase_id` values, record phrase-buffer timing, and persist `phrases.ndjson`.
- [x] 3.2 Record translation start/completion, observable queue depth or logical pending counts, and full enriched events in `translations.ndjson`.
- [x] 3.3 Instrument Piper synthesis for TTS start, first generated audio, and synthesis completion; instrument output for playback start/completion and persist `playback.ndjson`.
- [x] 3.4 Record unavailable physical queue depths as null without estimating them, while preserving adjacent timestamps for derived wait time.

## 4. Derived metrics and lifecycle handling

- [x] 4.1 Produce one `segments.ndjson` terminal record per source `segment_id`, including all available timestamps, queue observations, and multi-segment phrase lineage.
- [x] 4.2 Calculate stage durations, time to first TTS audio, queue/wait times, end-to-end playback-start/completion latency, and ASR/TTS RTF values.
- [x] 4.3 Preserve partial trace evidence and finalize the manifest/segment states for normal completion, interruption, worker failure, post-start trace-write failure, and trace-queue overflow.
- [x] 4.4 Report the trace directory at startup and fail before microphone capture if initial trace setup is unavailable.

## 5. Verification and operator documentation

- [x] 5.1 Add unit tests for private run allocation, unique IDs, monotonic timestamp handling, null unavailable fields, queue observations, derived metric calculations, and non-blocking trace-queue overflow.
- [x] 5.2 Add integration-style tests that trace multi-segment phrases through ASR, buffering, translation, TTS, playback, and terminal metrics.
- [x] 5.3 Add fixture-based analysis tests that demonstrate a stable-delay run, short-lived jitter, and a positive latency slope caused by downstream backlog.
- [x] 5.4 Document the directory and NDJSON schema, `/tmp` privacy/retention limitation, and how to create the latency-over-session and per-segment breakdown visualizations.
- [x] 5.5 Defer a short traced-versus-untraced physical-hardware comparison to the next live evaluation; it is outside this instrumentation change.
- [x] 5.6 Defer physical microphone/Piper demo verification to the next live evaluation; targeted trace tests and the full project suite completed for this change.
