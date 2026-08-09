## Context

The installed Whisper CLI transcribes complete audio files; it does not expose partial-word streaming through the current wrapper. The prototype can still provide useful near-live output by recording sequential short chunks, passing each chunk to local Whisper, and printing each completed result.

## Goals / Non-Goals

**Goals:**

- Run as a foreground long-lived process until Ctrl-C or a termination signal.
- Use the default microphone initially and show completed English transcript lines in the terminal.
- Keep audio local and reuse the installed Whisper executable and configured model path.
- Make chunk length configurable, with an initial approximately 3-second default.

**Non-Goals:**

- True word-by-word partial hypotheses, speaker diarization, recording/archive storage, translation, captions distribution, network input, or a macOS launchd service.

## Decisions

### Chunked near-live processing

The command will capture fixed-duration PCM WAV chunks and process them serially with the existing local Whisper wrapper. This gives predictable, inspectable behavior and avoids replacing the established Whisper installation. The expected visible delay is at least one chunk plus transcription time.

Alternative: use a purpose-built Whisper streaming implementation. It may reduce latency, but would introduce a different runtime and is premature before validating basic microphone capture.

### Foreground process first

The first command will be a process the user starts in a terminal and stops with Ctrl-C. "Daemon" behavior such as automatic background startup and restart belongs in a later deployment-focused change.

### Default system microphone

The initial version will use the default input device. Device listing and explicit selection can be added once basic permissions and capture are confirmed.

## Risks / Trade-offs

- [Terminal or IDE lacks microphone permission] → Detect and report the capture error with macOS permission guidance.
- [Whisper processing takes longer than each chunk] → Print a lag warning and use bounded temporary storage rather than accumulating unbounded audio.
- [Chunk boundaries split phrases] → Treat the initial transcript as experimental and evaluate chunk duration before adding overlap or context handling.
