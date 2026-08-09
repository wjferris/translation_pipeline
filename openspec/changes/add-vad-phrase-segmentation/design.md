## Context

The known-good live baseline captures continuously and sends a 5-second Whisper window every 4 seconds. It is intentionally simple, but output events can begin or end in the middle of a spoken sentence. The downstream phrase buffer cannot reliably repair ASR revisions after text is emitted.

## Goals / Non-Goals

**Goals:**

- Keep capture continuous while using detected speech pauses to choose ASR boundaries.
- Provide an opt-in `--segmentation vad` mode; retain `fixed` as the default and existing behavior.
- Run VAD entirely on the appliance and bound latency with maximum phrase duration.
- Produce the same finalized text/NDJSON shape as existing microphone transcription.
- Make VAD thresholds explicit and practical to tune with church speech and program audio.

**Non-Goals:**

- Replacing Whisper, solving every ASR error, altering the phrase buffer/translator, streaming partial revisions, separating speakers, filtering music, TTS, or changing AV routing.

## Decisions

### Use local WebRTC VAD for pause segmentation

Use the maintained Python packaging of WebRTC VAD (`webrtcvad-wheels`) against 16 kHz mono PCM frames. It runs locally, is lightweight enough for the appliance, and makes speech/non-speech decisions before the more expensive Whisper invocation. This is a boundary detector, not a new transcription model.

### Make VAD an explicit alternative, not the new default

`transcribe-microphone --segmentation vad` enables phrase segmentation. `fixed` remains the default, preserving the Medium 5-second/every-4-seconds baseline and providing a direct comparison. VAD-specific options are ignored or rejected outside VAD mode as appropriate.

### Segment on silence with guardrails

The VAD segmenter will retain a short pre-roll before detected speech, end a phrase after a configurable run of silence (initial target: 0.7 seconds), and force a phrase at a configurable maximum duration (initial target: 10 seconds). It discards very short non-speech fragments and flushes active speech cleanly when stopped.

The resulting phrase event timing reflects the actual captured phrase rather than an arbitrary fixed window. A VAD pause naturally adds its silence threshold to end-to-end delay.

### Preserve the existing downstream stream contract

VAD emits the same finalized English events currently accepted by `buffer-phrases` and `translate-stream`. No new server, port, queue, or pipeline command is introduced.

## Risks / Trade-offs

- [Quiet speech may be classified as silence] → Expose VAD aggressiveness and phrase-silence controls; compare against the fixed baseline using the same reading.
- [Music, room noise, or a live mixer signal keeps VAD active] → Force a maximum phrase duration and retain fixed mode as fallback.
- [Natural pauses add delay] → Start with a short threshold and measure quality versus latency rather than optimizing on a benchmark.
- [Native VAD dependency does not build on a target OS] → Validate macOS development and Ubuntu deployment installation before adopting VAD as a default.

## Migration Plan

No migration is required. Existing commands and fixed-window defaults remain unchanged. If VAD regresses accuracy or latency, users stop passing `--segmentation vad`; no rollback of the working pipeline is needed.

## Rollback Plan

Before implementation, create a timestamped snapshot under `backups/` containing
every file the change will alter, including `transcribe_microphone.py`, project
dependency configuration/lock files, and relevant README text. Include a
`RESTORE.md` with exact copy-back commands and `uv sync` as the final restore
step.

If VAD cannot install, misidentifies church speech, adds unacceptable latency,
or destabilizes fixed-window mode, stop the test, restore that snapshot, run
`uv sync`, and continue with the known-good fixed pipeline. The test command is
opt-in, but the snapshot protects against accidental changes to shared code and
dependencies without relying on source control.
