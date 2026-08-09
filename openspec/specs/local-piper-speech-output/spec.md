# local-piper-speech-output Specification

## Purpose
TBD - created by archiving change add-local-piper-speech-output. Update Purpose after archive.
## Requirements
### Requirement: Speak translated Spanish events locally
The system SHALL provide a `speak-stream` command that reads newline-delimited JSON events containing Spanish `text` from standard input, synthesizes each non-empty text value with a local Piper voice, and plays the resulting audio through the default local output device.

#### Scenario: Speak a translated event
- **WHEN** `speak-stream` receives a valid Spanish event and its selected Piper model is available
- **THEN** it SHALL play the synthesized Spanish phrase once through the local output device

#### Scenario: Preserve spoken order
- **WHEN** the worker receives multiple valid Spanish events
- **THEN** it SHALL synthesize and play them in input order without overlapping playback

### Requirement: Keep local speech output observable and resilient
The command SHALL write diagnostics to standard error, continue after malformed input, and provide actionable failures for missing voice models or local output-device errors.

#### Scenario: Invalid input event
- **WHEN** an input line is malformed JSON or lacks a non-empty string `text`
- **THEN** the command SHALL report the issue on standard error and continue reading later lines

#### Scenario: Missing voice model
- **WHEN** the selected Piper model file cannot be found
- **THEN** the command SHALL exit before playback with a message that identifies the missing path and explains that a local Piper voice is required

