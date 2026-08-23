## Why

Some USB line-input adapters expose a fixed 0 dB hardware gain on macOS. Their raw signal can be audible but too quiet for reliable voice activity detection and Whisper transcription; the live capture command needs an explicit, local software gain control.

## What Changes

- Add a `--input-gain-db` option to `transcribe-microphone` to amplify or attenuate captured microphone samples before segmentation and transcription.
- Keep the default gain at 0 dB so existing commands retain their current behavior.
- Validate the configured gain and prevent amplified samples from exceeding the supported audio range.
- Make the selected gain visible at startup so operators can confirm the capture configuration.

## Capabilities

### New Capabilities

<!-- No new capability; this extends live microphone transcription. -->

### Modified Capabilities

- `live-microphone-transcription`: Allow callers to configure bounded local software gain for captured microphone audio.

## Impact

- Affects the `transcribe-microphone` CLI and shared microphone capture callback in `src/live_audio_translation/transcribe_microphone.py`.
- Applies to both fixed-window and VAD segmentation, including the browser demo that consumes its NDJSON output.
- Does not alter the selected macOS input device, source hardware gain, local-only processing guarantee, or default zero-gain behavior.
