## Context

The prototype already has independent, local stages for microphone transcription, phrase buffering, Spanish translation, and Piper speech. They compose well from the command line:

```text
transcribe-microphone → buffer-phrases → translate-stream → speak-stream
```

This remains valuable because it is transparent and easy to troubleshoot. The demo should add a human-friendly display without replacing that path or requiring an internet connection.

## Goals / Non-Goals

**Goals:**

- Provide a clear non-technical demonstration of live English-to-Spanish translation.
- Show English transcription and Spanish translation side by side in a browser.
- Continue producing Spanish Piper speech through a selected local audio device.
- Run entirely on the local Mac after models and dependencies have been downloaded.
- Keep the CLI pipeline available unchanged.

**Non-Goals:**

- Zoom integration, virtual microphones, networked browser access, multi-room distribution, user accounts, persistent recordings, a general-purpose control panel, or production broadcast controls.
- Partial word-by-word rendering, terminology customization, adaptive VAD, audio mixing, or changes to ASR/translation/TTS model behavior.

## Proposed Architecture

Add a demo-only coordinator that receives recognized English phrase events and fans them out to the display and existing local workers.

```text
Wireless English input / microphone
              ↓
        Whisper + VAD
              ↓ English event
       local demo coordinator
        ├─ browser display: English pane
        └─ TranslateGemma
                 ↓ Spanish event
           ├─ browser display: Spanish pane
           └─ Piper → selected Mac output → remote-room speaker
```

The coordinator and browser server bind to loopback (`localhost`) by default. The browser display receives events over a local WebSocket or equivalent server-sent event channel. No event text or audio leaves the computer.

## Decisions

### Keep CLI mode as the canonical baseline

Do not modify or remove `transcribe-microphone`, `buffer-phrases`, `translate-stream`, or `speak-stream`. They remain independently runnable and continue to communicate with NDJSON. Demo mode is a separate entry point that composes their behavior through Python APIs or an internal event bridge.

### Use a deliberately simple bilingual display

The first display is a full-screen-friendly web page with two equal vertical panes:

- left: **English — Live Transcript**;
- right: **Español — Traducción en vivo**.

The newest completed phrase is prominent, with a limited scrolling history above it. Type must be large, high contrast, and readable from a short distance. A small connection/status label may indicate listening, translating, or speaking, but no technical log should be shown to the audience.

### Preserve completed-phrase timing

The initial display shows the same completed phrase events already used by VAD and translation. English naturally appears first; Spanish and spoken audio follow after translation. Do not invent partial text or attempt to conceal this intentional delay.

### Make audio output explicit

Demo mode should accept a Piper output-device option and pass it to the existing speech stage. This supports the planned physical separation: English arrives wirelessly at the laptop and Spanish plays in another room, avoiding acoustic feedback.

### Favor a one-command local launch

The future entry point should start the coordinator and open or print the local browser URL. It may be called `demo` or `run-demo`; the exact command name can be chosen during implementation. It should fail clearly when a required model, Ollama service, microphone, or audio device is unavailable.

## Risks / Trade-offs

- [Browser layer masks a pipeline failure] → Keep CLI mode available and make basic status visible to the operator.
- [Spanish display/audio lags behind English] → This is expected with phrase-based translation; retain bounded display history and evaluate with real speakers before optimizing.
- [Remote speaker accidentally feeds back into input] → Use the separate-room wireless output during demos and keep microphone/input routing explicit.
- [Local server is exposed on a network] → Bind only to loopback by default; network access is out of scope.
- [More UI becomes a distraction] → Keep the initial page display-only and defer controls until a real test demonstrates a need.

## Validation Plan

Future implementation should demonstrate all of the following on a network-disconnected Mac:

1. Launch the browser demo with locally installed models.
2. Feed a short spoken English sample through the selected input.
3. Confirm completed English phrases appear in the left pane.
4. Confirm their Spanish translations appear in the right pane.
5. Confirm the same Spanish phrases play sequentially on the explicitly selected output device.
6. Confirm the existing CLI-only pipeline still works unchanged.

## Rollback Plan

This is additive. Before implementation, confirm the current Git commit is a clean baseline. If the browser demo is unreliable, stop using its launcher or revert its dedicated commit(s); the established terminal pipeline remains available without modification.
