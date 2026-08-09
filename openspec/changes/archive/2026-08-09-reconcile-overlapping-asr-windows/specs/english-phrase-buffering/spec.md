## MODIFIED Requirements

### Requirement: Buffer English ASR events into translation-ready phrases
The system SHALL provide a `buffer-phrases` command that reads finalized English NDJSON events from standard input, retains one newest event until a successor can reconcile its overlapping words, and emits NDJSON phrase events containing stable accumulated English text on standard output.

#### Scenario: Reconcile an overlapping successor window
- **WHEN** a pending ASR event and its successor contain a multiword overlap at their adjacent boundary
- **THEN** the command SHALL commit the shared words only once and SHALL use the successor wording for the recognized overlap before phrase emission

#### Scenario: Reconcile hyphenated overlap
- **WHEN** a successor begins with word components that overlap the hyphenated ending of the pending event, such as `eight-year-old son` followed by `old son who`
- **THEN** the command SHALL not emit the repeated `old son` text twice

#### Scenario: Release a completed sentence
- **WHEN** reconciled accumulated input text contains a sentence-ending `.`, `?`, or `!`
- **THEN** the command SHALL emit the text through the last such boundary and retain any later unfinished text for subsequent input

#### Scenario: Preserve phrase traceability
- **WHEN** the command emits a phrase built from one or more input events with identifiers and timing
- **THEN** the output SHALL contain a phrase identifier, `source_ids`, `start_ms`, `end_ms`, and the accumulated `text`

### Requirement: Bound buffering delay
The command SHALL flush reconciled unfinished accumulated text and any pending ASR event after its configured maximum wait and when standard input closes.

#### Scenario: Timeout flush
- **WHEN** unfinished input text or a pending ASR event has waited at least the configured maximum without a successor or sentence boundary
- **THEN** the command SHALL emit the available phrase text and continue accepting later input

#### Scenario: End-of-input flush
- **WHEN** standard input closes with a pending ASR event or unfinished text buffered
- **THEN** the command SHALL reconcile and emit all remaining text before exiting
