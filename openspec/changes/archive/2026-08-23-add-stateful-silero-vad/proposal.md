## Why

The current Silero option runs Whisper-integrated VAD independently over overlapping fixed windows, then reconstructs transcript timing and text across the window boundaries. Recorded evaluation showed substantially less coherent output than WebRTC: short fragments, repeated boundary words, and lost ASR context. Silero should instead detect speech continuously and submit each completed local phrase to Whisper once.

## What Changes

- Replace the current overlapping-window implementation behind the `silero` VAD backend with a continuous, stateful local Silero speech segmenter.
- Keep `webrtc` as the default VAD backend and retain the existing runtime backend selector, so WebRTC and Silero remain comparable alternatives in one shared live translation pipeline.
- Emit bounded, padded Silero speech phrases for one local Whisper transcription each; remove cross-window Silero transcript reconstruction from this runtime path.
- Update the recorded VAD evaluator so its Silero replay follows the same continuous segmentation behavior as the live path.
- Document Silero-specific prerequisites and phrase-boundary tuning, while preserving the existing WebRTC-only tuning behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-vad-backend-selection`: redefine the Silero selection from Whisper-integrated overlapping windows to a continuous local stateful segmenter.
- `voice-activity-phrase-segmentation`: require the selected Silero backend to produce local, bounded, padded speech phrases from continuous audio.
- `recorded-vad-evaluation`: replay the stateful Silero phrase-segmentation path rather than the retired overlapping-window reconciliation path.

## Impact

- Affects microphone segmentation and recorded-evaluation code, especially `transcribe_microphone.py` and `tools/evaluate_recorded_vad.py`.
- Adds a local runtime dependency and model asset for continuous Silero inference; Whisper, its Metal/GPU configuration, translation, TTS, display, and external command shape remain unchanged.
- Requires unit, recorded-fixture, and live smoke validation for both selectable VAD backends.
