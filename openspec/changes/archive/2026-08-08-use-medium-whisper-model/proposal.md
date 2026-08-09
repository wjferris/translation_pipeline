## Why

The installed MacPorts Whisper package now provides `medium.bin`, while the project still defaults to the removed `small.bin`. The mismatch prevents normal transcription commands from starting.

## What Changes

- Change the project default model path to the installed Medium model.
- Update the local environment configuration and documentation.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `local-whisper-transcription`: Set the installed Medium model as the default local model.

## Impact

- Updates `.env`, the Python fallback setting, and README model references.
