## Context

MacPorts replaced the Small model file with `/opt/local/share/whisper/models/medium.bin`. Both the `.env` setting and Python fallback must match it so the project works consistently.

## Goals / Non-Goals

**Goals:**

- Use Medium as the default installed model.
- Retain `WHISPER_MODEL_PATH` as an override for another local model.

**Non-Goals:**

- Download, benchmark, or manage additional models.

## Decisions

Set `/opt/local/share/whisper/models/medium.bin` in both the source fallback and `.env`. This lets commands work whether or not the environment file was sourced.

The wrapper will also pass `/opt/local/lib` as a fallback dynamic-library path
to Whisper. MacPorts variant changes can replace the executable without its
required runtime search path, even though the `ggml` libraries remain installed.

## Risks / Trade-offs

- [Medium is slower and larger] → The configuration remains an overrideable local path for later comparisons.
- [A MacPorts variant replacement can remove Whisper's library search path] → Set a fallback library path only for the wrapper's Whisper subprocess.
