## Context

The project supports `WHISPER_MODEL_PATH` as a local override. Both Small and Medium are installed, and current experiments indicate a 5–6 second chunk-duration range.

## Goals / Non-Goals

**Goals:**

- Select Small for the next comparison run.
- Preserve the ability to switch back to Medium without reinstalling either model.

**Non-Goals:**

- Change the Python fallback or delete models.

## Decisions

Change only `WHISPER_MODEL_PATH` in `.env` to `small.bin`. Users must source `.env` in a new shell before running the command.

## Risks / Trade-offs

- [A shell may retain an earlier environment value] → Document sourcing `.env` before the test command.
