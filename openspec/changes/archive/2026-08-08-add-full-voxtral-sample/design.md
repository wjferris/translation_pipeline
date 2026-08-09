## Context

The project already provides an 8-second excerpt from the public `winning_call.mp3` file referenced by Mistral's Voxtral documentation. The user now needs the original full clip for a longer transcription check.

## Goals / Non-Goals

**Goals:**

- Store the unmodified public source MP3 locally under `src/resources/`.
- Document a copy-and-run command for it.

**Non-Goals:**

- Add additional datasets, change the transcription implementation, or assess transcription quality.

## Decisions

The sample will be saved as `voxtral-winning-call.mp3`, preserving the source filename's content and distinguishing it from `voxtral-winning-call-8s.mp3`.

## Risks / Trade-offs

- [The resource is larger than the short fixture] → It remains small enough for a source-controlled example and is suitable for a more representative smoke test.
