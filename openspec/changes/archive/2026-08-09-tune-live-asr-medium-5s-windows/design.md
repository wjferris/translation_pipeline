## Context

The current live baseline uses Small Whisper with a 4-second window every 3 seconds. The local MacPorts installation also has `medium.bin`. Capture remains continuous regardless of the selected window/stride values.

## Goals / Non-Goals

**Goals:**

- Use Medium Whisper by default for the next quality-focused test.
- Use a 5-second window every 4 seconds, retaining one second of overlap.

**Non-Goals:**

- Changing continuous capture, buffering, translation, TTS, or installing another model.

## Decisions

### Use a 5-second window with a 4-second stride

The window must be longer than the stride to retain overlap. This setting provides one second of repeated source audio while adding only one second of window context relative to 4/3.

## Risks / Trade-offs

- [Medium has higher compute cost] → This is a local quality experiment; the existing CLI options retain the ability to test Small or other windows.
