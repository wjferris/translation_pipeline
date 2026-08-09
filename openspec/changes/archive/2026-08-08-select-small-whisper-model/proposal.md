## Why

Both Small and Medium are now installed. The project needs a controlled Small-model comparison at the established 5–6 second chunk duration without removing Medium.

## What Changes

- Set the local `.env` Whisper model selection to Small.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `local-whisper-transcription`: Select the installed Small model through the project environment override for comparison testing.

## Impact

- Updates only the ignored local `.env` configuration; Medium remains installed and the Python fallback remains unchanged.
