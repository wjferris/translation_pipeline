## Context

`demo.py` uses background threads to forward English events and to translate and speak Spanish. The Spanish worker can be inside Piper/ONNX Runtime or `sounddevice` when Ctrl-C reaches the main thread. The current shutdown stops child processes but does not join those worker threads before the Python interpreter exits. On macOS, that has produced an `EXC_BAD_ACCESS` crash in the native CFFI/audio path during interpreter finalization.

## Goals / Non-Goals

**Goals:**

- Exit the demo without leaving active local worker threads behind.
- Ensure Piper playback returns and closes its audio stream before Python interpreter teardown.
- Stop browser event requests promptly and return control to the terminal predictably.
- Preserve the current CLI-only pipeline and normal demo behavior.

**Non-Goals:**

- Interrupting an already-playing Spanish phrase mid-audio.
- Changing TTS queue policy, ASR/VAD timing, model selection, browser UI, or audio routing.
- Diagnosing or modifying unrelated older microphone processes.

## Decisions

### Drain the current Spanish phrase rather than killing native audio

The demo will first stop accepting new work and terminate the microphone and phrase-buffer subprocesses. If Piper is already generating or playing one phrase, shutdown will allow that call to return normally. Forcing a native audio stream or ONNX call from another thread risks the same class of unsafe teardown that caused the crash.

The operator terminal will indicate that it is finishing the current phrase. With the demo's bounded VAD phrase duration, this should normally take only a short time.

### Retain explicit non-daemon worker thread references

`DemoPipeline` will retain the English-forwarding and Spanish-processing threads and join them during `stop()`. The main process must not continue to `Py_Finalize` while either thread can call Piper, ONNX Runtime, or `sounddevice`.

### Signal browser handlers to exit

The local event state will carry a shutdown signal that wakes Server-Sent Event handlers. The local HTTP server will stop accepting work only after the pipeline begins shutting down, and its lightweight browser-handler threads may be made daemon threads because they own no Piper/audio resources.

### Preserve a deterministic shutdown order

1. Receive Ctrl-C and publish a stopping status.
2. Stop new ASR input and close/terminate child CLI workers.
3. Join the English event-forwarder and Spanish translation/speech worker.
4. Wake and stop local browser event handlers, then stop and close the HTTP server.
5. Exit the main Python process after native Piper/audio work has completed.

## Risks / Trade-offs

- [Ctrl-C is not instantaneous while a phrase is playing] → Prefer a short, safe drain over a native-thread crash; show the operator what is happening.
- [A native dependency hangs indefinitely] → Report the waiting state and investigate the dependency rather than silently forcing Python finalization.
- [Browser handler remains connected] → Use an explicit shutdown signal and daemon-only handler threads so a browser tab cannot block audio cleanup.

## Validation Plan

1. Start the demo with the local Piper model and browser display.
2. Trigger Spanish speech, then press Ctrl-C while a phrase is actively playing.
3. Confirm the terminal reports orderly shutdown and returns to the shell without a macOS crash report.
4. Confirm no `demo`, `transcribe-microphone`, or `buffer-phrases` process remains afterward.
5. Repeat the start/stop cycle several times; verify the CLI-only pipeline still operates independently.

## Rollback Plan

Confirm a clean Git commit before implementation. The change is isolated to demo lifecycle code. If it introduces an unexpected shutdown hang, revert its commit; the existing CLI commands remain unchanged and can still be stopped independently.
