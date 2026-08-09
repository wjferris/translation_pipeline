## Why

The microphone experiment produces readable English only, while the translation worker accepts structured English events only. Connecting these local stages is the next proof point: spoken English at the microphone can become Spanish text continuously, with both stages still observable.

## What Changes

- Add a machine-readable NDJSON output mode to `transcribe-microphone` for finalized English transcription events.
- Retain a readable English transcript on standard error while NDJSON is sent to standard output.
- Document and verify a local shell pipeline from live microphone/Whisper ASR to `translate-stream`, resulting in Spanish text events.

## Capabilities

### New Capabilities

- `live-speech-text-translation`: Run the local microphone-to-Whisper-to-TranslateGemma text flow using standard streams.

### Modified Capabilities

- `live-microphone-transcription`: Provide a structured finalized-transcript output mode suitable for downstream processing.

## Impact

- Updates `transcribe-microphone` and its documentation.
- Uses the existing `translate-stream` process and local Ollama service; adds no dependency, server, port, TTS, or audio-output integration.
