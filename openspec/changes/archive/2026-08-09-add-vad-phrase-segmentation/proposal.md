## Why

Fixed Whisper windows provide continuous transcription but divide speech at arbitrary timer boundaries. A local voice-activity-based mode can wait for a natural pause before sending a phrase to Whisper, giving translation more complete English context and reducing sentence fragments.

## What Changes

- Add an opt-in voice-activity-detection (VAD) segmentation mode to `transcribe-microphone`.
- Turn continuous microphone audio into phrase-sized, pause-delimited Whisper inputs with bounded maximum duration.
- Preserve the current Medium Whisper 5-second/every-4-seconds fixed-window mode as the default baseline while VAD is evaluated.
- Document VAD settings, expected added pause latency, and a comparison procedure.

## Capabilities

### New Capabilities

- `voice-activity-phrase-segmentation`: Segment continuous local audio into bounded phrase recordings using locally executed VAD.

### Modified Capabilities

- `live-microphone-transcription`: Offer an opt-in VAD segmentation mode while retaining fixed-window defaults.

## Impact

- Updates the microphone transcription process and adds a local VAD dependency.
- Leaves the NDJSON protocol, phrase buffer, translation worker, TTS, OBS, and Zoom out of scope.
