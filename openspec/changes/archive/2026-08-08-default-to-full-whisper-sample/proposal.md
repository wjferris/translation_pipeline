## Why

The project now has a validated full-length bundled sample. Making it the default lets the developer repeat the baseline Whisper test with the shortest command while retaining custom-file support.

## What Changes

- Allow the Whisper command's audio argument to be omitted.
- Use the bundled 25-second sample when no audio path is given.
- Update the documented default command.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `audio-file-transcription`: Permit no audio argument and define the full bundled sample as its default.

## Impact

- Updates the local Whisper command interface and README usage.
