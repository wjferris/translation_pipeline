## Context

The current command loads Voxtral with Python libraries and Hugging Face cache files. The MacPorts Whisper installation provides `/opt/local/bin/whisper` and `/opt/local/share/whisper/models/small.bin`, allowing local transcription without a Python model runtime.

## Goals / Non-Goals

**Goals:**

- Provide `uv run transcribe-whisper audio-file` that emits only transcript text to standard output.
- Use the installed Whisper CLI and small model by default.
- Remove the Voxtral dependency chain and prune unused uv cache files.

**Non-Goals:**

- Downloading or managing Whisper models, live audio, translation, text-to-speech, or cross-platform Whisper installation.

## Decisions

The Python command will call `whisper` in a temporary directory with text-file output enabled, then print the generated transcript. This keeps the CLI's diagnostics out of standard output. The model path defaults to the known MacPorts location and can be overridden with `WHISPER_MODEL_PATH`.

Alternative: call Whisper directly. Its normal output mixes diagnostics with transcript text, which is less suitable for the future pipeline.

## Risks / Trade-offs

- [Whisper or its model is absent] → Validate both paths and present an actionable error.
- [The implementation is MacPorts-specific initially] → Document that this is a local Mac prototype; Linux packaging is a later concern.
