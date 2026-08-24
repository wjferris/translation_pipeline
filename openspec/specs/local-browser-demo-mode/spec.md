# local-browser-demo-mode Specification

## Purpose

Provide a local-only bilingual browser presentation that coordinates the existing English transcription, Spanish translation, and Piper speech pipeline.

## Requirements

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

### Requirement: Local-only operation

The browser demo SHALL bind to loopback by default and SHALL not require an internet connection after the required local models and dependencies are installed.

#### Scenario: Demonstrate with no network connectivity

- **WHEN** the computer has no internet connection and all required local services and model files are available
- **THEN** the demo can transcribe, translate, display text, and produce Spanish audio locally.

### Requirement: Preserve CLI baseline

The browser demo SHALL be additive and SHALL NOT remove or alter the independently runnable NDJSON CLI pipeline stages.

#### Scenario: Troubleshoot outside demo mode

- **WHEN** an operator runs the existing CLI transcription, translation, and speech commands
- **THEN** they continue to operate without starting the browser demo.

### Requirement: Selected Spanish audio output

The demo mode SHALL allow the operator to select the local device used for Spanish Piper audio output.

#### Scenario: Send Spanish audio to a separate room

- **WHEN** the operator starts demo mode with a selected local output device
- **THEN** Piper audio is sent to that device rather than an unintended default speaker.
