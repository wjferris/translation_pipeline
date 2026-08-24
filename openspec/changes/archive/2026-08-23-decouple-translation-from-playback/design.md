## Context

The browser-demo coordinator currently reads a translation-ready phrase, calls the local translation model, publishes Spanish text, and then calls the blocking Piper/output path in one loop. Piper synthesis and real-time device writes keep that loop busy, so later phrases remain unread in the phrase-buffer pipe. In trace `2026_08_23_001`, the source produced one completed segment about every 5.22 seconds while translation plus Piper work averaged 5.89 seconds; the resulting translation-start wait grew to roughly 70 seconds.

## Goals / Non-Goals

**Goals:**

- Ensure a completed Spanish translation is available to the browser without waiting for previous audio playback.
- Keep normal Spanish audio sequential and locally generated.
- Bound audible backlog so the application does not keep speaking increasingly stale translations during overload.
- Make playback admission, queue age, and skipped-audio decisions measurable in the existing trace.

**Non-Goals:**

- Change ASR, VAD, translation or Piper model selection, model prompts, language behavior, or audio-device routing.
- Parallelize Piper playback or interrupt an already-playing phrase.
- Alter the standalone NDJSON command pipeline.

## Decisions

### Split the coordinator into translation and playback stages

The coordinator will retain one translation worker and add one playback worker connected by an in-memory speech-job queue. The translation worker publishes Spanish text to the browser immediately after translation completes, records its translation trace event, and enqueues a speech job without waiting for Piper. The playback worker is the only caller of `play_text`, retaining one-at-a-time speech and device ownership.

Adding multiple concurrent Piper workers was rejected because overlapping Spanish speech is unintelligible and risks output-device contention. Keeping the current single loop was rejected because it makes browser translation availability depend on audio duration.

### Make the playback queue finite and freshness-oriented

The speech-job queue will have a documented finite capacity. Under normal load, jobs are admitted and played FIFO. If a new job arrives when the queue is full, the oldest unstarted job is evicted and recorded as skipped before admitting the newest job. The active phrase is never interrupted. Browser text remains complete even when its corresponding audio is skipped.

This explicit freshness policy is chosen because retaining every phrase creates unbounded, stale spoken output once playback is slower than incoming phrases. Blocking translation is rejected because it recreates the measured backlog; silently dropping either old or new audio is rejected because the operator and trace need to know that audible coverage was incomplete.

### Treat audio overload as an operator-visible condition

Each admission, dequeue, and skip records queue item count and oldest queued-job age. A skip changes the browser/operator status to an actionable audio-backlog warning and produces a trace lifecycle event. The status returns to normal after the queue drains. The warning reports the condition without exposing translated text to the audience-only display.

### Keep tracing lightweight and distinguish translation from audio latency

Existing phrase IDs and source-segment lineage remain the correlation keys. The trace will record translation completion, speech-job enqueue/dequeue, playback start/completion, and explicit `audio_skipped` terminal states. Derived metrics will distinguish time to Spanish display/translation availability from time to audible playback. Queue instrumentation remains boundary-only and uses the existing non-blocking writer.

## Risks / Trade-offs

- [Audible Spanish can omit a phrase under sustained overload] → Preserve all browser translations, evict only unstarted jobs, report every skip, and make the condition visible to the operator.
- [A finite item count does not exactly represent speech seconds] → Record item count and oldest-job age; calibrate the default capacity from repeatable traces.
- [Worker shutdown loses queued speech] → Stop intake first, finish or explicitly finalize queued jobs, and write terminal trace states.
- [New thread/queue lifecycle races] → Use one owner for each queue, deterministic stop sentinels, and integration tests for ordering, overflow, failure, and interruption.

## Migration Plan

1. Add the new queue and worker boundaries behind the existing demo entry point without changing command-line options or models.
2. Verify normal FIFO speech and immediate browser Spanish publication with deterministic tests.
3. Run a repeatable long-source trace and compare its latency slope with `2026_08_23_001`.
4. Roll back by restoring the former single downstream loop; existing trace directories remain readable because new fields are additive.

## Open Questions

- The initial default is three unstarted phrases; verify against a repeatable long-source test that it caps audible staleness while allowing normal short jitter without skips.
