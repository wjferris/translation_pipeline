## ADDED Requirements

### Requirement: Timed demo startup splash
The local browser demo SHALL render an audience-facing, full-screen startup splash before revealing the live bilingual transcript display. The splash SHALL remain visible for six seconds after the browser page is loaded, then reveal the existing live display without requiring operator or audience input.

#### Scenario: Demo page starts
- **WHEN** an operator launches the demo and opens its local browser URL
- **THEN** the page displays the startup splash instead of the live bilingual transcript display
- **AND** the page automatically reveals the live display after six seconds

#### Scenario: Transcript events arrive during startup
- **WHEN** English or Spanish transcript events arrive while the splash is visible
- **THEN** the page retains them using its normal transcript-history behavior
- **AND** displays the retained transcript history when the splash is removed

### Requirement: Startup loading and version information
The startup splash SHALL show a loading or readiness status and locally sourced runtime metadata, including the configured Ollama translation-model identifier and the Ollama server version when available. The system SHALL show a clear unavailable value for any optional metadata that cannot be obtained, without preventing the demo from starting or the splash from completing.

#### Scenario: Local metadata is available
- **WHEN** the local Ollama service and configured translation model provide version metadata
- **THEN** the splash displays the configured model identifier and the available Ollama and model version information

#### Scenario: Optional metadata is unavailable
- **WHEN** a version lookup for Ollama or the configured model fails or returns no version value
- **THEN** the splash labels that value as unavailable
- **AND** the page still reveals the live bilingual transcript display after six seconds

### Requirement: Local-only startup metadata endpoint
The demo coordinator SHALL provide the splash with its startup metadata through the existing loopback-only demo HTTP server and SHALL not require a cloud service or direct browser connection to Ollama.

#### Scenario: Browser requests startup metadata
- **WHEN** the startup splash loads in the browser
- **THEN** it retrieves the selected model and best-effort local version metadata from a loopback-only demo-server route
- **AND** it does not make a network request to an external service
