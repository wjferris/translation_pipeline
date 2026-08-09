## Why

The current live process pauses microphone capture while each Whisper chunk is transcribed and uses non-overlapping windows. Continuous speech can therefore be missed during processing or cut at a chunk boundary.

## What Changes

- Replace sequential record-then-transcribe behavior with continuous microphone capture and a background transcription worker.
- Generate overlapping audio windows and remove duplicate overlap text before display.
- Make Ctrl-C reliably stop capture and any active Whisper child process.
- Surface warning status if transcription falls behind live capture.

## Capabilities

### New Capabilities

- `overlapped-live-transcription`: Preserve continuous microphone audio through overlapping Whisper windows and produce de-duplicated transcript output.

### Modified Capabilities

- `live-microphone-transcription`: Change the live command from sequential chunk capture to continuous capture with reliable interruption.

## Impact

- Reworks the microphone capture and Whisper invocation flow while retaining local-only processing.
- Adds a bounded in-memory queue and overlap-text reconciliation.
