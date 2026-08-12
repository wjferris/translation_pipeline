## Why

When the browser demo starts, its presentation screen appears before the local translation components are visibly ready. A short startup splash will give the audience a deliberate loading experience and show the local software and model versions that underpin the demonstration.

## What Changes

- Add a full-screen startup splash to the local browser demo that is displayed when the demo page opens.
- Keep the splash visible for a short, fixed presentation interval of 5–7 seconds before revealing the bilingual transcript display.
- Show startup/loading progress and local runtime metadata in the splash, including the Ollama version and selected translation-model version or identifying tag.
- Make unavailable version information clear in the splash without preventing the demo from starting.

## Capabilities

### New Capabilities

- `demo-startup-splash`: Present a timed startup screen with loading status and local runtime/model version information before the browser demo becomes active.

### Modified Capabilities

- None.

## Impact

- Affects the Python demo coordinator's browser payload or local metadata lookup, and the demo HTML, CSS, and JavaScript assets.
- Uses the already-local Ollama service to obtain version or model identity where available; no cloud dependency is introduced.
- The existing `demo` command and `scripts/run-demo` launcher remain the demo entry points.
