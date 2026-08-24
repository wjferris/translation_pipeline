# Live Transcription Trial Notes

**Dates:** 2026-08-08 through 2026-08-14
**Status:** Early local prototype observations; not a production configuration.

## Beta version

![Beta version](beta-version.png)

[Watch the beta-version demo](IMG_1076.MOV)

## Setup used

- Source-built upstream Whisper CLI (`whisper.cpp`) available as `whisper` on `PATH`
- Local Whisper Medium model: `ggml-medium.bin`, selected with `WHISPER_MODEL_PATH`
- Local Silero VAD model for comparison: `ggml-silero-v6.2.0.bin`
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

### Integrated Silero VAD trial (2026-08-14)

The source-built Whisper CLI's integrated Silero VAD was added as an explicit
runtime option while retaining Python/WebRTC as the default baseline:

```sh
./scripts/run-demo --vad-backend silero
```

Early runs exposed overlap and boundary-word issues because each live capture
window is independently transcribed. The working implementation requests
Whisper's full JSON token output, calibrates its VAD-compressed timing back to
the original audio timeline, and emits only tokens extending beyond the prior
overlapping window. In the final live confirmation, Silero was near-perfect and
subjectively produced more natural phrase boundaries than the Python/WebRTC
baseline. Continue sustained-talk testing before changing the default backend.

### Piper local-speech trial (2026-08-09)

The Mexican-Spanish Piper voice was connected to the live VAD → Whisper →
translation stream and played through local output. The first end-to-end run
performed well enough to establish local Spanish speech as the next working
baseline. Longer listener tests should still evaluate voice naturalness,
listening fatigue, and terminology pronunciation before any Zoom routing.

### Full-discourse live demo trial (2026-08-23)

The end-to-end system worked well overall in a live test. The gain-controlled
USB line input provided a usable source, and the browser demo, transcription,
translation, and Piper output operated together.

The WebRTC VAD phrase-end setting required speaker-specific tuning. A value
between `0.3` and `0.45` seconds was useful, but the appropriate setting varied
with the speaker's pace: faster speakers favored a shorter threshold, while
other speakers needed more silence to avoid premature phrase endings. Treat
`--vad-silence-seconds` as a live-test control to watch and adjust rather than a
single universal value.

The largest issue was accumulated end-to-end delay during a sustained talk. The
test ran for the final speaker's full discourse; by the end, the translated
output was nearly two minutes behind the speaker. This indicates backlog over
the full pipeline rather than a tolerable per-phrase delay and is the highest
priority issue for the next live evaluation.

### Decoupled playback browser trial (2026-08-23)

After separating translation from Piper playback, a repeatable long-source
browser run (`2026_08_23_002`) was compared with the prior full-discourse trace
(`2026_08_23_001`). The run used Silero VAD with `0.35` seconds of silence,
30 dB input gain, and a Spanish playback-queue capacity of three unstarted
jobs.

| Measure | Prior run (`001`) | Decoupled run (`002`) |
| --- | ---: | ---: |
| Source span | 10.0 min | 12.73 min |
| Playback-start latency, median | 42.58 s | 3.79 s |
| Playback-start latency, P95 | 69.75 s | 9.31 s |
| Playback-start latency, maximum | 73.51 s | 12.56 s |
| Playback-latency slope | +7.15 s/min | approximately 0 s/min |

The translation worker did not accumulate a wait before translation in the
second run. Short-lived Spanish playback-queue bursts remained visible, but
they drained rather than growing through the talk. The queue reached its
capacity of three and evicted three unstarted speech jobs (affecting four
source segments); one was a blank-audio cue and two were spoken Spanish
phrases. Their browser translations were still displayed. The selected default
capacity remains three: it keeps spoken audio fresh while making any overload
explicit in the trace instead of letting it become sustained delay.

The run demonstrates that audio output can still have short, bounded jitter,
but the prior cumulative backlog was removed. Future tuning should compare a
capacity of four with the same VAD setting, balancing fewer skipped spoken
phrases against older audio.

## Known limitations

- The initial implementation uses the default macOS input device. It does not yet list or explicitly select audio interfaces/mixer inputs.
- The microphone signal is still the main quality variable; compare a saved continuous recording with live-capture windows before drawing model conclusions.
- Python/WebRTC remains the default backend while the newer Silero path receives longer live-event testing.
- Silero timing reconciliation depends on the supported `whisper.cpp` full-JSON output contract; an incompatible CLI fails before microphone capture.

## Next experiments

1. Run a sustained 5–10 minute English talk with both WebRTC and Silero, noting accuracy, lag, and listening-relevant errors.
2. Decide whether the live demo default should switch from WebRTC to Silero.
3. Add explicit input-device selection and basic input-level visibility.
4. Evaluate continuous overlapping windows against a saved continuous recording of the same speech.
5. Measure timestamped capture, ASR, translation, and Piper stages during a full discourse to locate and reduce accumulated end-to-end backlog.
