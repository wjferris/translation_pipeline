## Why

The current CLI pipeline is a strong, fully local engineering baseline, but it is difficult for a non-technical audience to follow from terminal output alone. A simple browser display will make the live English transcription, Spanish translation, and Spanish audio demonstrable without changing the working CLI workflow.

## What Changes

- Add a separate local browser demo mode that displays live English and Spanish text in a full-screen-friendly, vertically split layout.
- Introduce a local event coordinator so one recognized English phrase can be delivered to the browser, translation worker, and Piper speaker output without relying on a single shell pipeline.
- Keep the existing NDJSON commands and CLI pipeline operational and documented as the troubleshooting baseline.
- Allow demo-mode audio to target a deliberate local output device, such as the wireless feed to a separate Spanish-speaking room.

## Capabilities

### New Capabilities

- `local-browser-demo-mode`: Run a local-only bilingual browser display and Spanish audio demo using the existing ASR, translation, and Piper stages.

### Modified Capabilities

- None.

## Impact

- Adds a small local web application and browser-facing event stream in a future implementation.
- Preserves the current command-line programs and NDJSON event format.
- Requires no cloud service, external account, Zoom connection, or AV-system redesign.
- Introduces a local browser as a presentation surface only; it is not a production broadcast interface.
