# Live Transcription Trial Notes

**Date:** 2026-08-08  
**Status:** Early local prototype observations; not a production configuration.

## Setup used

- Local MacPorts Whisper CLI (`whisper.cpp`)
- Local Whisper Medium model: `/opt/local/share/whisper/models/medium.bin`
- `transcribe-microphone` command, which records short microphone chunks and transcribes them locally
- Dedicated microphone rather than the Mac's ambient default input

## Observations

### Audio input matters first

The Mac's default microphone captured ambient sound and incidental media. Whisper produced noise labels such as music and footsteps, plus unreliable plausible text. Switching to a dedicated microphone improved the result substantially.

### Model choice

Medium remained fast enough for the local prototype and gave a better starting point for the dedicated-microphone trials. Small and Medium are both installed.

Small was also tried with longer 5–6 second chunks. Increasing Small's chunk duration did not make its transcription comparably accurate. In informal, non-scientific observation, Medium was by far the better model for the dedicated-microphone tests. Treat Medium as the preferred working baseline unless later controlled comparisons say otherwise.

### Chunk-duration trials

| Chunk duration | Observation |
| --- | --- |
| 3 seconds | Fast, but dropped phrases and had weak context. |
| 4 seconds | Still felt too short for the desired transcription quality. |
| 5 seconds | Noticeably better; current practical baseline. |
| 6 seconds | Quality was good, but added delay. |
| 5–6 seconds | Current estimated sweet-spot range. Test 5.5 seconds next. |

The chunk-duration observations above describe Medium trials. Longer chunks were also tried with Small, but did not close the observed accuracy gap to Medium.

Run a specific trial with:

```sh
uv run transcribe-microphone --chunk-seconds 5.5
```

## Current baseline

Use a dedicated microphone, the Medium model, and approximately 5–6 second chunks. This is an observational baseline rather than a controlled benchmark. It is near-live transcription, not word-by-word captions: visible delay is one collected chunk plus Whisper processing time.

### VAD phrase-segmentation trial (2026-08-09)

The same local Medium Whisper and translation pipeline was also tested with
pause-based segmentation:

```sh
uv run transcribe-microphone --segmentation vad --vad-silence-seconds 0.45 --output-format ndjson | uv run buffer-phrases | uv run translate-stream
```

In an informal live church-talk reading, pause-delimited phrases were a much
better listener/viewer experience than the fixed overlapping windows. The test
showed no noticeable loss of English recognition accuracy, and the previously
visible duplicate/overlap fragments were not observed. The pause-based latency
felt natural and preferable to translating arbitrary short windows. Keep the
fixed Medium 5/4 mode as a comparison fallback while more talks are evaluated.

## Known limitations

- The initial implementation uses the default macOS input device. It does not yet list or explicitly select audio interfaces/mixer inputs.
- The microphone signal is still the main quality variable; compare a saved continuous recording with live-capture windows before drawing model conclusions.
- Fixed-window overlap de-duplication is conservative and may still leave repeated text or miss a difficult boundary phrase; VAD mode reduced this in the initial trial.

## Next experiments

1. Switch the project environment back to Medium before continuing live trials.
2. Run a sustained 5–10 minute English talk and note accuracy, lag, and listening-relevant errors.
3. Add explicit input-device selection and basic input-level visibility.
4. Evaluate continuous overlapping windows against a saved continuous recording of the same speech.
5. Repeat the VAD comparison with 0.45 and 0.5 seconds of phrase-end silence over a sustained 5–10 minute talk.
