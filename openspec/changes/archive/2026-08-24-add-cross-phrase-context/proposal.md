## Why

The paired-video evaluation showed that isolated phrase processing can lose
meaning at boundaries and mishandle names and LDS-specific wording. Bounded
prior text can condition local Whisper and TranslationGemma without delaying
the live pipeline or introducing cloud dependencies.

## What Changes

- Add a bounded, configurable English transcript history that is supplied to
  each subsequent local Whisper invocation as decoder context.
- Add a bounded, configurable sequence of completed English/Spanish phrase
  pairs to the local TranslationGemma chat history before translating the next
  phrase.
- Keep contextual text separate from the current phrase event and ensure that
  only the current phrase's Spanish translation is emitted.
- Add operator-visible controls, diagnostics, tests, and documentation for the
  context windows and their reset behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `live-microphone-transcription`: condition each local Whisper transcription
  with a bounded history of prior finalized English phrases.
- `streaming-text-translation`: condition each local TranslationGemma request
  with a bounded history of completed phrase translations while preserving
  stream-safe output.

## Impact

- Affects `transcribe_microphone.py`, the shared Whisper command adapter, and
  `translate_stream.py`.
- Adds CLI configuration and context-state handling to the transcription and
  translation workers, plus unit coverage and README guidance.
- Keeps audio and text local: Whisper remains local and TranslationGemma
  continues to use the configured local Ollama service.
