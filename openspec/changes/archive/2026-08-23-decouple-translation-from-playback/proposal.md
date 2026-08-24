## Why

The 2026-08-23 timing trace shows end-to-end delay growing from roughly 4 seconds to 72 seconds. Translation averaged 0.64 seconds per phrase, but it could not begin the next phrase until the same worker completed Piper synthesis and playback, which averaged 5.26 seconds.

## What Changes

- Separate translation from Piper synthesis/playback into independently scheduled downstream stages.
- Allow translated Spanish text to reach the browser promptly without waiting for prior Spanish audio to finish.
- Preserve ordered Spanish audio playback while making its queue age and depth observable.
- Bound playback backlog and report overload explicitly; do not silently discard translated speech.
- Retain the existing local-only models, CLI pipeline, VAD behavior, phrase ordering, and timing-trace format as the measurement baseline.

## Capabilities

### New Capabilities

- `decoupled-translation-playback`: Independently scheduled translation and ordered Spanish-audio playback with explicit, bounded downstream backpressure.

### Modified Capabilities

- `local-browser-demo-mode`: Publish completed Spanish translations to the browser independently of the audio playback schedule.
- `live-pipeline-timing-traces`: Record downstream-stage queue observations that distinguish translation availability from delayed Spanish audio playback.

## Impact

- Affects browser-demo orchestration and the handoff between translation, Piper synthesis, and audio output.
- Adds bounded in-memory queues, lifecycle handling, and timing/health reporting; no cloud service or model change is required.
- Does not change the standalone NDJSON command behavior in this change.
