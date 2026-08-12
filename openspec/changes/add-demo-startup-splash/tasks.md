## 1. Local startup metadata

- [ ] 1.1 Add a loopback-only demo-server route that returns the configured translation-model identifier and best-effort local Ollama/runtime metadata with stable unavailable fallbacks.
- [ ] 1.2 Implement bounded, failure-tolerant Ollama version and selected-model metadata lookup without making it a prerequisite for starting the pipeline.
- [ ] 1.3 Add focused coordinator tests for available and unavailable startup-metadata responses.

## 2. Browser startup presentation

- [ ] 2.1 Add semantic startup-splash markup above the existing bilingual display, including loading status and runtime/model metadata fields.
- [ ] 2.2 Style the splash as a responsive, full-screen overlay and ensure the underlying live display is not presented as active until startup completes.
- [ ] 2.3 Fetch and render the local startup metadata, retain live event history during startup, and remove the splash automatically after a six-second timer.
- [ ] 2.4 Add browser-asset tests or a manual verification procedure covering the timer, available/unavailable metadata states, and early transcript events.

## 3. Documentation and verification

- [ ] 3.1 Document the startup splash and displayed local metadata in the local-browser-demo section of the README.
- [ ] 3.2 Run the relevant automated tests and launch the demo to verify the splash lasts six seconds, shows correct data or unavailable fallbacks, and transitions to the live display.
