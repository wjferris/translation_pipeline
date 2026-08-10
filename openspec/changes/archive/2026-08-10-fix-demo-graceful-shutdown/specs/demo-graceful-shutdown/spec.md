## ADDED Requirements

### Requirement: Graceful local demo shutdown

The system SHALL provide an optional demo-mode entry point that serves a browser display from the local computer and renders completed English transcript events and their completed Spanish translations in separate vertical panes. When the operator stops demo mode, the system SHALL stop new input, safely finish any in-progress local Piper playback, and exit without leaving demo worker processes running.

#### Scenario: Display a translated phrase

- **WHEN** demo mode receives a completed English phrase and its translated Spanish event
- **THEN** the English text appears in the English pane and the Spanish text appears in the Spanish pane
- **AND** the display remains readable in a full-screen browser window.

#### Scenario: Stop during Spanish playback

- **WHEN** the operator presses Ctrl-C while Piper is generating or playing a Spanish phrase
- **THEN** demo mode stops accepting new phrases
- **AND** waits for the current Piper call to release its local resources
- **AND** returns to the shell without a Python native-thread crash or a leftover demo worker.
