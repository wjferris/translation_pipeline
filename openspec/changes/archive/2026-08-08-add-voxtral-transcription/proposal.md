## Why

The project needs a small, observable first building block for its planned English-to-Spanish audio pipeline. Transcribing a recorded audio file locally establishes that audio input and English speech recognition work before translation or speech synthesis are introduced.

## What Changes

- Add a command-line Python script that accepts one audio-file path.
- Load a local Voxtral speech-recognition model and print its transcript to standard output.
- Provide a reproducible project command and only the dependencies required for this transcription experiment.
- Include a short public audio sample for a repeatable first transcription run.
- Include the audio-decoding dependency required by Voxtral's local Transformers path.
- Load already-downloaded model files locally by default, with an explicit option for intentional Hugging Face downloads.

## Capabilities

### New Capabilities

- `audio-file-transcription`: Transcribe a supported audio file with Voxtral and emit plain text to standard output.

### Modified Capabilities

- None.

## Impact

- Adds a runnable Python entry point and its model-runtime dependencies.
- Updates the project documentation with setup and usage for the transcription experiment.
- Requires an initial model download when the script is first run.
- Adds a small MP3 test fixture under `src/resources/`.
