# streaming-text-translation Specification

## Purpose
TBD - created by archiving change add-ollama-text-translation-worker. Update Purpose after archive.
## Requirements
### Requirement: Translate finalized English text events locally
The system SHALL provide a `translate-stream` command that reads newline-delimited JSON events containing finalized English text from standard input and emits newline-delimited JSON events containing Spanish translations to standard output using the local `translategemma:4b` Ollama model.

#### Scenario: Successful translation
- **WHEN** the worker receives `{"id":"segment-1","text":"Good morning."}` on standard input and local Ollama is available
- **THEN** it SHALL emit one JSON line with `id` equal to `segment-1` and `text` containing only the Spanish translation

#### Scenario: Preserve event timing
- **WHEN** an input event includes `start_ms` and `end_ms`
- **THEN** the corresponding output event SHALL retain those fields unchanged

### Requirement: Keep the translation worker stream-safe
The worker SHALL write only JSON event lines to standard output and SHALL write diagnostics, model status, and errors to standard error.

#### Scenario: Worker used in a pipe
- **WHEN** a caller redirects the worker's standard output to another process
- **THEN** each non-empty output line SHALL be valid JSON

### Requirement: Handle malformed input and local inference failures
The worker SHALL continue processing subsequent input lines after malformed JSON, missing required text, or a local Ollama inference failure, and SHALL emit a structured error event for the affected line when an event identifier is available.

#### Scenario: Invalid JSON input
- **WHEN** an input line is not valid JSON
- **THEN** the worker SHALL report the issue on standard error and continue reading the next line

#### Scenario: Ollama unavailable
- **WHEN** a valid input event is received but local Ollama cannot produce a translation
- **THEN** the worker SHALL emit a JSON error event retaining the input event identifier and continue reading later messages

### Requirement: Condition translations with bounded completed phrase history
The system SHALL retain a bounded ordered history of successfully completed
English/Spanish phrase pairs during one `translate-stream` process and SHALL
provide the selected pairs as contextual chat history when translating the next
valid English phrase. It SHALL emit only the Spanish translation of the current
input event.

#### Scenario: Translate a phrase after a prior successful translation
- **WHEN** `translate-stream` receives a valid current English phrase after it
  has emitted one or more successful Spanish translations with context enabled
- **THEN** it SHALL send the selected prior English/Spanish pairs and the
  current English phrase to the local Ollama chat model
- **AND** it SHALL emit one Spanish NDJSON event for the current phrase only

#### Scenario: Start a fresh translation worker
- **WHEN** `translate-stream` starts a new process
- **THEN** it SHALL begin with an empty completed-phrase history and SHALL send
  its first valid phrase without prior translation pairs

#### Scenario: Disable translation phrase context
- **WHEN** an operator sets the translation context length to `0`
- **THEN** `translate-stream` SHALL omit prior phrase pairs from the model
  request and SHALL otherwise preserve the existing stream-safe output
  behavior

#### Scenario: Exclude unsuccessful work from context
- **WHEN** an input line is invalid or a translation request fails or returns
  no Spanish text
- **THEN** the system SHALL not add that input or error result to the completed
  phrase history used by later translations
