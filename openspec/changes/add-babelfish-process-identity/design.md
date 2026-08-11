## Context

`demo.py` owns the local browser server and starts microphone/ASR and phrase-buffer subprocesses. Translation and Piper playback run as threads inside the coordinator. This is a sound component boundary, but the operating system mostly displays generic Python process names, making it hard to distinguish a deliberate BabelFish run from an unrelated Python task.

## Goals / Non-Goals

**Goals:**

- Make the parent process identifiable as a BabelFish demo in terminal process listings and, where supported, Activity Monitor.
- Make child process roles recognizable as BabelFish ASR and BabelFish phrase buffer.
- Give all demo processes a shared lifecycle boundary so operators can inspect and terminate the complete run safely.
- Preserve the existing graceful Ctrl-C behavior.

**Non-Goals:**

- Combining all work into a single Python process.
- Renaming the underlying Whisper, Ollama, Piper, or macOS system processes.
- Creating a background daemon, Login Item, service manager configuration, GUI tray app, or production deployment system.
- Modifying the standalone CLI commands outside demo mode.

## Decisions

### Use a named parent plus role-specific children

The intended visible hierarchy is:

```text
Babelfish Demo
├─ Babelfish ASR
└─ Babelfish Phrase Buffer
```

The translation and Piper workers remain threads of `Babelfish Demo`, because they deliberately share the loaded Piper model and coordinator state. They do not need separate OS processes.

### Use a common process group or session for lifecycle control

The demo launcher/coordinator should establish a new process group or session before starting its children. The exact macOS-compatible mechanism will be chosen during implementation. The group supplements—not replaces—the current explicit graceful shutdown: stop new input, drain active Piper speech, join workers, then exit.

### Treat process-title display as best effort

macOS tools can differ in whether they show an executable name, command line, or mutable process title. Implementation should use a compatible local technique such as `setproctitle` only if it produces useful visibility on the target Mac. Regardless of title display, the parent/child relationship and common process group are the reliable operational controls.

### Keep standalone CLI commands generic

`transcribe-microphone`, `buffer-phrases`, `translate-stream`, and `speak-stream` continue to work independently and retain their existing names. BabelFish naming applies only to children launched by `demo`.

## Risks / Trade-offs

- [Activity Monitor does not display a mutable Python title] → Keep operator documentation based on parent PID/process group and terminal command line rather than relying exclusively on a visual label.
- [Process-group changes interfere with Ctrl-C] → Test Ctrl-C and child cleanup explicitly on macOS before treating the feature as complete.
- [A title helper adds unnecessary packaging complexity] → Prefer a minimal, well-supported dependency or a no-dependency command-line labeling technique; omit cosmetic title changes if they are unreliable.

## Validation Plan

1. Start `demo` and inspect the process tree with `ps` and Activity Monitor.
2. Confirm the BabelFish parent and each child role are distinguishable where supported.
3. Confirm workers share the expected parent/group relationship.
4. Stop the demo during active Piper playback and verify the existing graceful shutdown still completes with no orphaned BabelFish workers.
5. Confirm the individual CLI commands remain independently runnable.

## Rollback Plan

Make the implementation in a dedicated Git commit. If process naming or grouping has platform-specific problems, revert that commit; the current demo process model and graceful shutdown remain intact.
