## Context

The current flow is `transcribe-microphone --output-format ndjson | translate-stream`. Its English events correspond to overlapping Whisper windows, not linguistic sentences. The existing stream boundary lets us add a focused local process without coupling audio capture, ASR, or translation.

## Goals / Non-Goals

**Goals:**

- Read and write one JSON object per line.
- Accumulate English `text` from consecutive finalized ASR events.
- Emit completed text through the last `.`, `?`, or `!`; keep an unfinished tail for later context.
- Flush a tail after a configurable bounded wait and when input closes.
- Retain aggregate timing and source-event identifiers for debugging.

**Non-Goals:**

- Changing Whisper recognition, providing linguistic-perfect sentence splitting, revising already-emitted text, glossary logic, TTS, or persistent queues.

## Decisions

### Use a separate standard-stream process

`buffer-phrases` will sit between ASR and `translate-stream`:

```sh
uv run transcribe-microphone --output-format ndjson | uv run buffer-phrases | uv run translate-stream
```

This keeps components independently testable and avoids a custom API or service supervisor.

### Release punctuation-delimited text, with a timeout fallback

The buffer releases all accumulated text ending at its most recent sentence punctuation. It holds the remaining tail for additional ASR context. If no punctuation arrives before the maximum wait, it releases the available tail so live output cannot stall.

### Remove an obvious repeated boundary token

When a new ASR event begins with the same normalized word that ended the prior event and either occurrence has sentence-ending punctuation, the repeated leading word is discarded. This narrowly addresses overlap artifacts such as `assembly. assembly. For ...`; it intentionally does not attempt broad language correction.

## Risks / Trade-offs

- [ASR punctuation is wrong or absent] → The bounded timeout produces an imperfect but timely phrase.
- [A true rhetorical repeated word crosses a boundary] → Narrow duplicate removal only applies when punctuation signals an apparent completed phrase.
- [Longer phrase buffering adds delay] → Default maximum wait is short and configurable.
