## 1. Capture configuration

- [x] 1.1 Add the `--input-gain-db` floating-point CLI option with a `0 dB` default and reject values outside -48 dB through +48 dB before opening the microphone.
- [x] 1.2 Calculate the configured linear gain factor once and include the selected decibel value in the microphone startup status.
- [x] 1.3 Forward the optional input-gain setting through the browser demo's microphone-worker invocation.

## 2. Audio processing

- [x] 2.1 Apply the configured gain to every captured callback block before it is queued for fixed-window, WebRTC VAD, or Silero VAD processing.
- [x] 2.2 Clip amplified and attenuated samples to the normalized `[-1.0, 1.0]` range while preserving the existing zero-gain capture behavior.

## 3. Verification

- [x] 3.1 Add unit tests for zero gain, positive gain, attenuation, and clipping behavior in the capture path.
- [x] 3.2 Add command-argument tests for valid boundary values and invalid out-of-range values.
- [x] 3.3 Run the targeted microphone-transcription test suite and the full project test suite.
