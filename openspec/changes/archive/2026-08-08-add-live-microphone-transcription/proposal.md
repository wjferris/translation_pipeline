## Why

Recorded-file transcription proves the model path, but the next experiment needs to show whether local Whisper can keep up with speech captured from a microphone. A visible, continuously updating transcript is the smallest useful live-audio proof of concept.

## What Changes

- Add a long-running microphone-transcription command that stays active until interrupted.
- Capture audio from the default system microphone in short chunks and transcribe each chunk locally with Whisper.
- Print completed transcript lines continuously to the terminal.
- Keep recurring Whisper status messages out of the live transcript display.

## Capabilities

### New Capabilities

- `live-microphone-transcription`: Capture microphone audio continuously and display local Whisper transcripts with a bounded chunking delay.

### Modified Capabilities

- None.

## Impact

- Adds a microphone-audio dependency and a new long-running command.
- Requires macOS microphone permission for the terminal or IDE that launches it.
- Does not change the existing recorded-file transcription command.
