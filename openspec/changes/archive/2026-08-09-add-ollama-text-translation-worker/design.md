## Context

The appliance architecture separates capture, ASR, translation, and TTS. The immediate need is the boundary between finalized English text from ASR and Spanish text for future TTS. Ollama 0.32.6 and `translategemma:4b` are already installed locally on the development Mac.

## Goals / Non-Goals

**Goals:**

- Run as a long-lived local process until standard input closes or it is interrupted.
- Consume one finalized English message per input line and emit one corresponding Spanish message per output line.
- Preserve a caller-provided message identifier and optional timing fields.
- Use only the existing local Ollama service; do not add a custom server, port, or web framework.
- Produce Spanish translation only, without model commentary or formatting.

**Non-Goals:**

- Audio capture, ASR, partial-text revision handling, TTS, glossary retrieval, persistent queues, concurrent translation requests, or remote Ollama use.

## Decisions

### Use newline-delimited JSON over stdin/stdout

Input and output will each use one JSON object per line. This is easy to inspect manually, works with pipes, retains event identity/timing, and avoids creating a new network API. Input shape: `{"id":"...","text":"...","start_ms":0,"end_ms":5000}`. Successful output retains supplied metadata and replaces `text` with Spanish text. Diagnostics are written only to standard error.

### Use the Ollama Python client with TranslateGemma

The worker will call the installed local Ollama service with `translategemma:4b` using a fixed translation prompt that requests only Spanish output. The process itself listens on no port. Calling the client directly is preferable to spawning `ollama run` once per line because it has structured responses and reuses Ollama's loaded-model lifecycle.

### Process finalized events sequentially

The initial worker processes input lines in order, one at a time. This preserves spoken sequence and creates an observable baseline before adding batching or concurrency.

## Risks / Trade-offs

- [Ollama is not running or the model is absent] → Return an actionable per-message error and continue reading later messages where possible.
- [Translation inference is slower than ASR event arrival] → Preserve ordered input/output first; measure backlog before adding queueing or concurrency.
- [ASR errors propagate into Spanish] → Keep English input and Spanish output visible in the stream for evaluation.
- [Translation prompt may emit extra text] → Enforce a narrow fixed prompt and test output formatting.
