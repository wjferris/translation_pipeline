## 1. Downstream-stage separation

- [x] 1.1 Introduce a correlated Spanish speech-job type and one finite, configurable in-memory playback queue owned by the demo coordinator.
- [x] 1.2 Refactor the coordinator so the translation worker publishes Spanish browser events and enqueues speech jobs without calling Piper or waiting for audio playback.
- [x] 1.3 Add one sequential playback worker that owns Piper/output-device access and preserves FIFO order for admitted jobs.

## 2. Bounded audio-backlog behavior

- [x] 2.1 Implement the documented default playback-queue capacity and validate its demo configuration.
- [x] 2.2 On a full queue, evict and finalize the oldest unstarted job, admit the newest job, retain browser text, and never interrupt active playback.
- [x] 2.3 Surface audio-backlog and recovery status to the operator without exposing diagnostic text in the audience display.
- [x] 2.4 Finalize admitted, skipped, failed, and interrupted jobs safely during normal shutdown and worker failure.

## 3. Timing and observability

- [x] 3.1 Extend trace stage events and terminal metrics with speech-job enqueue/dequeue observations, queue item count, oldest queued-job age, and audio-skipped states/reasons.
- [x] 3.2 Preserve separate translation-availability and audible-playback latency in NDJSON outputs and update the timing-trace documentation.

## 4. Verification

- [x] 4.1 Add deterministic unit tests for immediate Spanish publication, FIFO playback, one-at-a-time Piper access, full-queue eviction, and no interruption of active playback.
- [x] 4.2 Add lifecycle and trace tests for queue age/depth, audio-skipped lineage, playback failure, interruption, and recovery status.
- [x] 4.3 Run the focused tests and full project suite.
- [x] 4.4 Run a repeatable long-source browser demo, compare latency slope and audio-skip observations with trace `2026_08_23_001`, and document the selected default queue capacity.
