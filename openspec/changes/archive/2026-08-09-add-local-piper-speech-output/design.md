## Context

`translate-stream` emits Spanish NDJSON events, while Piper has already generated and played a local Mexican-Spanish WAV test. The next step is a persistent text-to-speech stage so Piper is loaded once and speaks successive translated phrases, rather than starting a new process for each phrase.

## Goals / Non-Goals

**Goals:**

- Read Spanish events continuously from standard input.
- Keep a single Piper voice model loaded for the process lifetime.
- Play each non-empty Spanish event sequentially through the default local output device.
- Keep diagnostics on standard error and handle malformed events/model/output failures without a traceback.
- Make the voice model path explicit and local.

**Non-Goals:**

- Zoom, virtual microphone routing, audio mixing, network streaming, speech interruption/barge-in, simultaneous speakers, voice cloning, automatic voice selection, or permanent recording.

## Decisions

### Add a dedicated `speak-stream` process

The new stage reads the existing translated NDJSON protocol:

```text
transcribe-microphone → buffer-phrases → translate-stream → speak-stream → local speakers
```

It consumes the Spanish `text` field, uses Piper's Python API to synthesize audio, and plays that audio with the existing `sounddevice` dependency. This keeps TTS independent from translation and leaves a clear boundary for later virtual-audio output.

### Use local Piper model files, selected explicitly

The initial command uses an explicit local model path via `--model`, with a documented Mexican-Spanish example. Voice model files remain under ignored `models/` and are not downloaded or committed by the application.

### Serialize phrase playback

The worker plays one completed Spanish phrase at a time. This prevents overlapped speech and gives a clear baseline for measuring TTS throughput. If Piper or playback falls behind, report the condition; queue policy and interruption behavior are deferred until real tests show a need.

### Retain the Spanish event boundary

Piper may generate raw PCM internally, but the first prototype sends audio directly to the local playback device. It does not expose a raw stdout audio protocol yet; later virtual-output work can introduce that deliberately.

## Risks / Trade-offs

- [Spanish output is captured again by the microphone] → Use headphones for local testing; later use a mix-minus/virtual audio route.
- [Voice is distracting or mismatched with speaker] → Treat the selected voice as an evaluation baseline; audition other voices before production use.
- [TTS generation/playback is slower than incoming text] → Start sequentially and observe backlog before adding queue/drop/interruption policies.
- [Local model path is missing] → Fail early with an actionable message explaining how to download/select a Piper voice.

## Rollback Plan

Confirm a clean committed Git baseline before implementation. The new command is additive and does not change the known-good English-to-Spanish-text pipeline. If speaker output is unsuitable, stop using `speak-stream` or restore the Git baseline; translation-only operation remains available.
