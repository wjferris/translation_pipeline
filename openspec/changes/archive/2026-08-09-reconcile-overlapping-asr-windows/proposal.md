## Why

The phrase buffer improves translation context, but it currently commits each Whisper event before the following overlapping window can confirm or correct its trailing words. This produces repeated text and isolated fragments in Spanish when adjacent ASR windows disagree.

## What Changes

- Extend `buffer-phrases` to retain one uncommitted ASR window before releasing text for phrase buffering and translation.
- Reconcile adjacent ASR windows using normalized word alignment, including hyphenated-word components, before committing stable English text.
- Retain bounded-delay and end-of-input behavior so the live flow cannot stall.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `english-phrase-buffering`: Reconcile one overlapping successor ASR window before committing text into translation-ready phrases.

## Impact

- Updates the local `buffer-phrases` process and its tests/documentation.
- Adds approximately one ASR stride of intentional latency before translation; no model, service, or audio-routing changes.
