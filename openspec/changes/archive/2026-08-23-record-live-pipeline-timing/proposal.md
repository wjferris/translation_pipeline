## Why

A full live discourse accumulated nearly two minutes of translated-output delay. The current pipeline has no correlated, high-resolution measurements, so it cannot distinguish a stable expected delay from jitter, queue growth, or a stage that is slower than real time.

## What Changes

- Assign a unique `segment_id` to every captured audio segment or utterance and preserve its lineage through phrase buffering, translation, TTS, and playback.
- Record high-resolution monotonic timestamps at source audio, VAD, ASR, translation, TTS, and playback boundaries, plus queue depth when a stage exposes a queue.
- Persist complete stage NDJSON outputs and one derived metric record per segment in an identifiable, private `/tmp/babelfish-live-runs/YYYY_MM_DD_NNN` directory for each demo run.
- Enable tracing by default while allowing an explicit `--no-timing-trace` baseline run for controlled observer-effect comparison.
- Calculate source duration, stage durations, queue/wait times, ASR and TTS real-time factors, and source-to-playback start/completion latency.
- Define a trace schema that supports later end-to-end latency-over-session and per-segment latency-breakdown visualizations.
- Keep measurement overhead minimal by collecting only segment/stage-boundary events and moving all trace I/O to a background writer.
- Keep the change observational: do not alter model selection, stage ordering, retry behavior, or latency optimization policy.

## Capabilities

### New Capabilities

- `live-pipeline-timing-traces`: Local, high-resolution per-segment instrumentation that measures and attributes live translation latency.

### Modified Capabilities

<!-- No existing behavioral requirement changes; this is a diagnostic capability layered over the current pipeline. -->

## Impact

- Affects demo orchestration and the microphone/VAD, ASR, phrase-buffer, translation, Piper TTS, and playback boundaries.
- Writes sensitive spoken/transcribed text and timing data locally under `/tmp/babelfish-live-runs/` with owner-only permissions; raw audio remains out of scope.
- Uses no per-audio-frame logging, synchronous trace writes, or per-record durable flushes in the live processing path.
- Adds no network calls and makes no automatic performance or model-selection changes.
