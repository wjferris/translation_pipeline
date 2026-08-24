## MODIFIED Requirements

### Requirement: Local bilingual browser demo
The system SHALL provide an optional demo-mode entry point that serves a browser display from the local computer and renders completed English transcript events and their completed Spanish translations in separate vertical panes. Once a Spanish translation completes, the demo SHALL publish it to the Spanish pane independently of the schedule of Spanish Piper synthesis or playback.

#### Scenario: Display a translated phrase

- **WHEN** demo mode receives a completed English phrase and its translated Spanish event
- **THEN** the English text appears in the English pane and the Spanish text appears in the Spanish pane
- **AND** the display remains readable in a full-screen browser window.

#### Scenario: Display translation while earlier audio is active

- **WHEN** an earlier Spanish phrase is still being synthesized or played
- **AND** a later Spanish translation completes
- **THEN** the later translation SHALL appear in the Spanish pane without waiting for the earlier audio to finish.
