## 1. Shutdown coordination

- [x] 1.1 Add an explicit shutdown signal for pipeline and browser event workers.
- [x] 1.2 Retain and join the English-forwarding and Spanish translation/speech threads during demo shutdown.
- [x] 1.3 Stop input subprocesses before waiting for the active Piper phrase to complete.

## 2. Browser lifecycle

- [x] 2.1 Wake Server-Sent Event handlers during shutdown and configure the local server so browser connections cannot block audio cleanup.
- [x] 2.2 Show an operator-facing stopping/finishing status during graceful shutdown.

## 3. Validation and documentation

- [x] 3.1 Repeatedly stop the demo during active Piper playback and confirm it exits without a macOS crash report or leftover demo workers.
- [x] 3.2 Verify the CLI-only pipeline remains independently runnable.
- [x] 3.3 Document the safe Ctrl-C shutdown behavior and any known wait time.
