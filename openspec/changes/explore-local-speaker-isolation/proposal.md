## Why

The direct podium-microphone feed should limit room ambience, but loud audience
speech and transient sounds may still reach the ASR input. Before introducing a
new processing stage, the project needs an evidence-based way to assess whether
local speaker isolation or noise suppression improves live transcription more
than it harms speech fidelity or latency.

## What Changes

- Define a local-only evaluation of software and hardware-adjacent
  speaker-isolation/noise-suppression options placed before microphone capture.
- Establish representative test material, measurable acceptance criteria, and a
  documented decision record for direct feed versus an optional enhancement
  stage.
- Keep the existing direct input, VAD backends, and live demo unchanged during
  exploration; do not install, enable, or make a candidate a runtime default.

## Capabilities

### New Capabilities

- `local-speaker-isolation-evaluation`: Evaluate and record whether a local
  pre-ASR speech-enhancement option is suitable for the live translation
  pipeline.

### Modified Capabilities

None.

## Impact

- Adds an exploration plan, test evidence, and future integration decision.
- May later affect the selected macOS input device, local audio routing, and
  microphone capture setup, but causes no current code, dependency, or runtime
  change.
