## Why

Non-speech annotations such as `[blank audio]` can reach the Spanish text stream and are currently treated as ordinary text by Piper. Speaking those cues is distracting during the live demo and does not represent program audio.

## What Changes

- Suppress square-bracketed non-speech cues before text is sent to Piper synthesis.
- Skip playback when removing those cues leaves no speakable text.
- Preserve normal Spanish speech and the existing ordering guarantees for all remaining spoken text.
- Apply the behavior wherever the shared Piper playback function is used, including `speak-stream` and the browser demo.

## Capabilities

### New Capabilities

<!-- No new capability; this changes existing Piper speech-output behavior. -->

### Modified Capabilities

- `local-piper-speech-output`: Exclude square-bracketed non-speech cues from Piper synthesis while retaining ordinary spoken text.

## Impact

- Affects the shared Piper playback path in `src/live_audio_translation/speak_stream.py` and its use by `demo.py`.
- Requires focused regression coverage for cue-only and mixed spoken/cue text.
- Does not change transcription, translation, browser display, model selection, or audio-device configuration.
