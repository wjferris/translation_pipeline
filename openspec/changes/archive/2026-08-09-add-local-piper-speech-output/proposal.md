## Why

The pipeline now produces coherent Spanish text from live English speech. The next proof point is audible Spanish: turn those translated events into local speech so voice quality, pace, and end-to-end listener experience can be evaluated before introducing Zoom or virtual audio routing.

## What Changes

- Add a long-running `speak-stream` command that consumes Spanish NDJSON events and synthesizes them locally with Piper.
- Play synthesized Spanish audio through the default local speaker device, sequentially and without overlapping phrases.
- Provide model selection/configuration for the downloaded Mexican-Spanish Piper voice and document the end-to-end speaker test.

## Capabilities

### New Capabilities

- `local-piper-speech-output`: Synthesize translated Spanish event text with a locally installed Piper voice and play it through the local audio output device.

### Modified Capabilities

- None.

## Impact

- Adds a Python console command using the already-installed `piper-tts` and `sounddevice` dependencies.
- Requires a locally downloaded Piper voice model, kept outside Git.
- Does not add Zoom, virtual microphones, network audio, TTS voice cloning, or AV-system changes.
