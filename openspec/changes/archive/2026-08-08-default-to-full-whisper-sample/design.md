## Context

`transcribe-whisper` currently requires an audio path, even though the project includes a known 25-second sample that has already been tested successfully.

## Goals / Non-Goals

**Goals:**

- Make the full sample the default input.
- Preserve explicit audio-file input for real recordings.

**Non-Goals:**

- Change Whisper model selection or transcription behavior.

## Decisions

The positional `audio` argument becomes optional and defaults to the resource path computed relative to the package source file. This avoids dependence on the current working directory.

## Risks / Trade-offs

- [A developer might not realize a bundled sample is being used] → The help text and README will state the default explicitly.
