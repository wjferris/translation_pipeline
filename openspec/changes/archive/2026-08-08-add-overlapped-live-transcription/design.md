## Context

The current `transcribe-microphone` command records a complete chunk, waits for Whisper to finish, then starts the next recording. This creates capture gaps. The user observed dropped words with live microphone input despite strong continuous-file transcription, indicating that the live chunking design is the primary issue.

## Goals / Non-Goals

**Goals:**

- Capture microphone audio continuously while Whisper processes earlier windows.
- Use a configurable window duration and stride; default initial values should be 6 seconds and 5 seconds, creating a 1-second overlap.
- Print each new transcript portion once, suppressing duplicated overlap words where possible.
- Shut down both capture and active Whisper work cleanly on Ctrl-C.
- Warn when transcription lags capture instead of silently accumulating unlimited memory.

**Non-Goals:**

- Word-level timestamps, speaker diarization, voice activity detection, translation, a background launchd service, or perfect semantic reconciliation of repeated phrases.

## Decisions

### Producer-worker architecture

Use a `sounddevice` input callback as a producer that appends audio into a rolling buffer and emits windows into a bounded queue at the configured stride. A separate worker owns Whisper invocation. Capture therefore continues while the worker is busy.

Alternative: process each chunk in the callback. This would recreate the existing capture gap and risks audio callback overruns.

### Overlapping windows and token de-duplication

Each 6-second window starts 5 seconds after the prior one. The display layer compares normalized words at the suffix of the prior displayed transcript and prefix of the next result, then removes the longest matching boundary sequence. The algorithm is intentionally conservative: uncertain matches remain visible rather than dropping potentially new speech.

### Bounded backlog

The window queue is bounded. When the worker cannot keep up, the process reports the lag on standard error; the exact drop/backpressure policy will be explicit in implementation and documented.

### Interrupt active Whisper work

Replace the blocking child-process call with a managed process handle so Ctrl-C can terminate the active Whisper invocation, join worker threads, and remove temporary files.

## Risks / Trade-offs

- [Medium may process more slowly than the stride] → Show queue/lag warnings and test with the target 5–6 second settings.
- [Overlap de-duplication can either repeat or lose words] → Use conservative word matching and save optional diagnostics in future work if needed.
- [Continuous audio callbacks add concurrency complexity] → Keep capture, queue, and transcription responsibilities separate and test graceful shutdown explicitly.
