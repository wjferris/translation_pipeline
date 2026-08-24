## 1. Demo event architecture

- [x] 1.1 Define the internal English and Spanish event fan-out interface while retaining NDJSON compatibility.
- [x] 1.2 Add an additive local demo coordinator and launcher command.
- [x] 1.3 Bind the display service to loopback by default and provide actionable startup diagnostics.

## 2. Browser display

- [x] 2.1 Create the full-screen-friendly two-pane English/Spanish display.
- [x] 2.2 Stream completed phrase events to the browser and retain a bounded readable history.
- [x] 2.3 Show minimal operator-facing state without exposing console logs to the audience.

## 3. Audio and validation

- [x] 3.1 Pass an explicit audio output-device choice from demo mode to Piper speech playback.
- [x] 3.2 Verify a complete offline demo using microphone or wireless input and separate-room Spanish output.
- [x] 3.3 Verify the existing CLI-only pipeline remains unchanged.

## 4. Documentation

- [x] 4.1 Document the demo launch, browser use, output-device selection, and feedback-avoidance setup.
- [x] 4.2 Add a short demo trial note with observed timing and listener feedback.
