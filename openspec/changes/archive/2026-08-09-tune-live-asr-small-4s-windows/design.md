## Context

Microphone capture is already continuous. Whisper receives overlapping fixed-length windows, currently defaulting to a 6-second window every 5 seconds. The local `.env` already selects `/opt/local/share/whisper/models/small.bin`.

## Goals / Non-Goals

**Goals:**

- Make a 4-second window every 3 seconds the default live-transcription cadence.
- Preserve the one-second overlap that helps avoid phrase-boundary loss.
- Keep all command-line overrides available for comparative testing.

**Non-Goals:**

- Changing capture continuity, Whisper installation/model files, translation behavior, audio hardware, or adding new buffering logic.

## Decisions

### Set 4 seconds / 3 seconds as the live default

This produces a 4-second Whisper window that begins every 3 seconds, retaining one second of overlap. It lowers baseline delay relative to 6/5 while preserving the successful overlap strategy.

Alternative: treat 3 seconds as a capture duration. Rejected because capture must remain continuous to avoid the phrase gaps found in the earlier sequential design.

## Risks / Trade-offs

- [Shorter windows reduce context] → Retain CLI overrides so Medium or longer-window comparisons remain straightforward.
- [Small Whisper makes occasional recognition errors] → This is an experimental default, not a claim that it is universally more accurate than Medium.
