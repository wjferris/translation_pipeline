## Why

Whisper's fixed audio windows produce useful finalized English text, but their boundaries do not reliably align with spoken sentences. Translating each window independently gives TranslateGemma too little context and creates awkward Spanish punctuation and fragments.

## What Changes

- Add a long-running NDJSON phrase-buffer command between ASR and translation.
- Combine consecutive English ASR events, release complete sentence-like phrases at natural punctuation, and flush unfinished text after a bounded wait or end of input.
- Preserve approximate timing and traceability in buffered output, and update the documented live pipeline.

## Capabilities

### New Capabilities

- `english-phrase-buffering`: Convert finalized but window-bound English ASR events into larger, translation-ready phrase events.

### Modified Capabilities

- `live-speech-text-translation`: Insert the phrase buffer into the documented microphone-to-Spanish-text pipeline.

## Impact

- Adds a `buffer-phrases` console command and documentation.
- Uses only local standard streams; no model, server, package, or audio-routing changes.
