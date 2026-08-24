## MODIFIED Requirements

### Requirement: Speak translated Spanish events locally
The system SHALL provide a `speak-stream` command that reads newline-delimited JSON events containing Spanish `text` from standard input, removes complete square-bracketed non-speech cue annotations from that text immediately before local Piper synthesis, and plays each remaining non-empty spoken value through the default local output device. The system SHALL preserve the input order of spoken values without overlapping playback. It SHALL not alter the event text used by other pipeline stages or the browser display.

#### Scenario: Speak a translated event
- **WHEN** `speak-stream` receives a valid Spanish event containing ordinary speech and its selected Piper model is available
- **THEN** it SHALL play the synthesized Spanish phrase once through the local output device

#### Scenario: Suppress a cue within a spoken phrase
- **WHEN** an event text contains complete square-bracketed content such as `[blank audio]` alongside Spanish speech
- **THEN** the system SHALL synthesize only the remaining Spanish speech and SHALL not synthesize the bracketed content

#### Scenario: Skip a cue-only event
- **WHEN** removing complete square-bracketed cues leaves no non-whitespace text
- **THEN** the system SHALL not invoke Piper synthesis or open an audio output stream, and SHALL continue with later events in order

#### Scenario: Preserve unmatched brackets
- **WHEN** an event text has an unmatched square bracket
- **THEN** the system SHALL retain that text for Piper synthesis rather than silently discarding it

### Requirement: Keep local speech output observable and resilient
The command SHALL write diagnostics to standard error, continue after malformed input, and provide actionable failures for missing voice models or local output-device errors.

#### Scenario: Invalid input event
- **WHEN** an input line is malformed JSON or lacks a non-empty string `text`
- **THEN** the command SHALL report the issue on standard error and continue reading later lines

#### Scenario: Missing voice model
- **WHEN** the selected Piper model file cannot be found
- **THEN** the command SHALL exit before playback with a message that identifies the missing path and explains that a local Piper voice is required
