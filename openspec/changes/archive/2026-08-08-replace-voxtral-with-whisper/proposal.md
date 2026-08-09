## Why

The project now has a locally installed Whisper CLI and model, which is simpler for the first transcription experiment than the Voxtral Python runtime. Replacing Voxtral also removes a large set of unused Python packages.

## What Changes

- **BREAKING** Replace `transcribe-voxtral` with `transcribe-whisper`.
- Invoke the local MacPorts `whisper` executable and its installed model through a thin Python wrapper.
- Remove Voxtral, Torch, Transformers, Hugging Face, and audio-decoding dependencies from the uv environment and prune their cache artifacts.

## Capabilities

### New Capabilities

- `local-whisper-transcription`: Transcribe one local audio file with the installed Whisper CLI and print plain text.

### Modified Capabilities

- `audio-file-transcription`: Change the transcription engine and command from Voxtral to the locally installed Whisper CLI.

## Impact

- Replaces the transcription module, console command, project dependencies, and documentation.
- Requires `whisper` and `/opt/local/share/whisper/models/small.bin` to remain installed on the host.
