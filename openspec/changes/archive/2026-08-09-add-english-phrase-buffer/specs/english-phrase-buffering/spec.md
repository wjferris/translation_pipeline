## ADDED Requirements

### Requirement: Buffer English ASR events into translation-ready phrases
The system SHALL provide a `buffer-phrases` command that reads finalized English NDJSON events from standard input and emits NDJSON phrase events containing accumulated English text on standard output.

#### Scenario: Release a completed sentence
- **WHEN** accumulated input text contains a sentence-ending `.`, `?`, or `!`
- **THEN** the command SHALL emit the text through the last such boundary and retain any later unfinished text for subsequent input

#### Scenario: Preserve phrase traceability
- **WHEN** the command emits a phrase built from one or more input events with identifiers and timing
- **THEN** the output SHALL contain a phrase identifier, `source_ids`, `start_ms`, `end_ms`, and the accumulated `text`

### Requirement: Bound buffering delay
The command SHALL flush unfinished accumulated text after its configured maximum wait and when standard input closes.

#### Scenario: Timeout flush
- **WHEN** unfinished input text has waited at least the configured maximum without a sentence boundary
- **THEN** the command SHALL emit the available phrase text and continue accepting later input

#### Scenario: End-of-input flush
- **WHEN** standard input closes with unfinished text buffered
- **THEN** the command SHALL emit the remaining text before exiting

### Requirement: Keep phrase buffering stream-safe
The command SHALL write only NDJSON events to standard output and diagnostics to standard error.

#### Scenario: Worker used in a pipe
- **WHEN** `buffer-phrases` is placed between ASR and translation processes
- **THEN** every non-empty standard-output line SHALL be valid JSON accepted by `translate-stream`
