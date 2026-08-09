## Why

The live transcription pipeline now produces increasingly reliable finalized English text. A separate local translation worker is needed to turn those events into Spanish text without coupling translation latency or model choice to audio capture and ASR.

## What Changes

- Add a long-running English-to-Spanish translation command using the locally installed `translategemma:4b` Ollama model.
- Accept finalized English text messages from standard input and write corresponding Spanish text messages to standard output.
- Use a documented newline-delimited JSON protocol, keeping diagnostics on standard error.

## Capabilities

### New Capabilities

- `streaming-text-translation`: Translate a continuous stream of finalized English text events to Spanish using local Ollama inference.

### Modified Capabilities

- None.

## Impact

- Adds the Ollama Python client dependency and a console command.
- Depends on the existing local Ollama service and installed `translategemma:4b` model.
- Adds no project-hosted HTTP server or listening port.
