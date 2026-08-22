## Why

The live microphone workflow makes it difficult to compare VAD implementations
reliably: every run has different speech, pauses, and room noise. A recorded
English WAV with its embedded subtitle transcript provides a repeatable local
fixture for evaluating WebRTC and Whisper-integrated Silero VAD before either
backend is used in a live event.

## What Changes

- Add a test-only, file-input VAD evaluation runner that replays a local 16 kHz
  mono WAV through the existing transcription/VAD components without opening an
  audio device.
- Support equivalent evaluation runs for the existing Python/WebRTC VAD
  baseline and the Whisper-integrated Silero VAD alternative.
- Emit timestamped, machine-readable transcript results so each backend can be
  compared with a supplied English SRT reference.
- Add a documented runtime script or flow that runs the same fixture through
  both backends and retains their outputs as test artifacts.
- Keep the fixture runner and its commands outside the production demo and
  live-microphone application path.

## Capabilities

### New Capabilities

- `recorded-vad-evaluation`: Repeatable local replay and comparison of VAD
  backends against a WAV input and subtitle reference.

### Modified Capabilities

- None.

## Impact

- New test/scaffold runner and a developer-facing script or documented flow.
- Reuses the existing local Whisper executable, model selection, WebRTC VAD,
  and Silero capability validation; no new service or cloud dependency.
- Adds generated evaluation artifacts that must remain out of version control.
