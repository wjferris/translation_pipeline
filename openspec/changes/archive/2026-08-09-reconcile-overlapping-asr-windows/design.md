## Context

Whisper uses overlapping audio windows, so consecutive finalized transcripts often contain the same words, sometimes with different punctuation or recognition quality. The current phrase buffer receives each event independently and can remove only a narrow exact duplicate. Once it emits a phrase, the translator has already produced Spanish text and cannot retract it.

## Goals / Non-Goals

**Goals:**

- Keep one incoming ASR event uncommitted until its successor arrives.
- Reconcile overlapping text before it enters sentence/timeout phrase buffering.
- Handle common token differences such as capitalization, terminal punctuation, and hyphenated words.
- Prefer the successor's wording within a recognized overlap, because it has later audio context.
- Preserve bounded waiting, traceability, JSON-stream safety, and clean end-of-input flushing.

**Non-Goals:**

- Full ASR confidence scoring, arbitrary transcript rewriting, correction of non-overlap recognition errors, speaker diarization, TTS, or a change to Whisper's audio windows.

## Decisions

### Hold one ASR event before committing it

`buffer-phrases` will retain the newest ASR event as a pending window. When the next event arrives, it aligns their overlapping text and commits only the reconciled stable material into its existing sentence buffer. At end of input or a bounded timeout, it flushes the pending event rather than waiting indefinitely.

This adds roughly one configured ASR stride of latency, but prevents the translation worker from receiving text that a following overlapping window immediately supersedes.

### Normalize for alignment, retain original wording for output

Alignment will compare lowercased word components with punctuation removed and hyphenated words split into components. Output retains the successor's original text outside removed overlap. A minimum multiword alignment threshold avoids treating ordinary single repeated words as overlap.

### Keep the current process boundary

The command remains `buffer-phrases`; the shell pipeline and JSON protocol stay the same. This is a behavioral improvement inside the existing buffer, not another service.

## Risks / Trade-offs

- [Adjacent windows disagree without enough shared words] → Do not invent a correction; retain both text portions and allow the phrase timeout/boundary logic to proceed.
- [Legitimate repeated phrases resemble overlap] → Require a multiword alignment and constrain matching to the adjacent-window boundary.
- [Extra held window increases delay] → Keep timeout flushing and make the added behavior observable in testing before further latency tuning.

## Migration and Rollback Plan

Before implementation, create a timestamped manual snapshot under
`backups/` of every file this change can alter: `buffer_phrases.py` and the
relevant README documentation. The snapshot is kept in the project, independent
of source control.

Test the changed buffer with the existing pipeline and a controlled reading.
If it creates worse duplication, missing phrases, or unacceptable delay, stop
the pipeline and restore the snapshot files with explicit `cp` commands recorded
in the backup's `RESTORE.md`. Then run `uv sync` and rerun the known-good command:

```sh
uv run transcribe-microphone --output-format ndjson | uv run buffer-phrases | uv run translate-stream
```

The rollback changes no model files, microphone settings, or translation-worker
configuration, so restoration is limited to the phrase-buffer behavior and its
documentation.
