## Context

`transcribe-microphone` currently prints final English text lines for a person to read. `translate-stream` already consumes newline-delimited JSON (NDJSON) events and emits corresponding Spanish events. The stages need a small, stable stream boundary without making audio capture depend on translation speed or adding a custom network service.

## Goals / Non-Goals

**Goals:**

- Preserve the current readable microphone-transcript experience.
- Add an opt-in ASR output mode that emits exactly one finalized English JSON event per line on standard output.
- Retain a caller-independent sequence identifier and approximate source-window timing in each event.
- Allow a single shell pipeline to run live ASR and translation continuously, with Spanish JSON as its final standard output.

**Non-Goals:**

- TTS, Spanish audio, OBS/Zoom/network integration, persistent services, process supervision, partial ASR revisions, glossary handling, or changing Whisper recognition behavior.

## Decisions

### Add an opt-in NDJSON mode to `transcribe-microphone`

`transcribe-microphone --output-format ndjson` will write only finalized English events to standard output. The default human-readable output remains unchanged. In NDJSON mode, the readable English transcript moves to standard error so it cannot corrupt the downstream stream.

Each event will have `id`, `text`, `start_ms`, and `end_ms`. IDs increment for one run. Timing describes the Whisper source window and is intentionally approximate when overlap removal leaves only part of a window.

Alternative: change the command's default output to JSON. Rejected because the current direct microphone experiment is useful and should remain simple to run.

### Compose existing processes with a shell pipe

The initial full flow will be documented as:

```sh
uv run transcribe-microphone --output-format ndjson | uv run translate-stream
```

The ASR process owns capture and produces English events; `translate-stream` owns local model calls and produces Spanish events. A pipe provides backpressure and process separation without adding ports, a queue, or another long-running application.

Alternative: add a combined Python supervisor now. Deferred because it introduces process lifecycle and signal-forwarding behavior unrelated to proving the text path.

### Keep diagnostics separate from stream data

Both commands reserve stdout for NDJSON in pipeline mode. Startup, Whisper/backlog warnings, readable English transcript, and failures go to stderr. This makes Spanish stdout immediately usable by a later TTS stage.

## Risks / Trade-offs

- [The translator is slower than ASR] → The OS pipe applies backpressure; observe latency before adding queues or concurrency.
- [Overlap removal makes window timing imprecise] → Preserve source-window timing and document it as approximate rather than invent word-level timestamps.
- [A shell pipeline needs both processes running] → Keep the command explicit and defer a supervisor until actual operational use requires one.
- [An ASR error produces no usable English event] → Report it to stderr and continue later microphone windows.
