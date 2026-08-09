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

