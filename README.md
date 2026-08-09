# Local Live Audio Translation

An experimental, local-first prototype for turning English program audio into intelligible Spanish spoken audio for live-event broadcasting.

## First goal

Prove a simple recorded-audio flow before connecting to OBS, Zoom, network audio, or the existing AV system:

```text
Recorded English speech
  -> English speech recognition
  -> English-to-Spanish text translation
  -> Spanish text-to-speech
  -> Spanish audio file
```

The initial work deliberately evaluates general translation quality only. LDS-specific terminology, names, scripture references, glossaries, corpus retrieval, and model fine-tuning are later phases.

## Prototype stack

```mermaid
flowchart TB
    A["English program audio<br/>from existing mixer / AV system"]
    B["Audio input<br/>USB interface or network stream"]
    C["English speech recognition<br/>Whisper or Voxtral"]
    D["English text"]
    E["Text translation<br/>NLLB-200"]
    F["Spanish text"]
    G["Spanish text-to-speech<br/>local TTS model"]
    H["Spanish audio output<br/>network stream or virtual audio device"]
    I["Existing OBS / AV infrastructure"]
    J["Spanish listeners<br/>Zoom / broadcast distribution"]

    A --> B --> C --> D --> E --> F --> G --> H --> I --> J

    K["Linux appliance with NVIDIA GPU<br/>uses existing hardware"] -. accelerates .-> C
    K -. accelerates .-> E
    K -. accelerates .-> G
```

## Principles

- Prefer local processing and models that can later run on Linux with an NVIDIA GPU.
- Favor translation accuracy and comfortable listening over the lowest possible latency.
- Keep the translation appliance narrowly scoped: audio in, Spanish audio out.
- Test competing approaches with the same recorded English material and native Spanish-speaker feedback.

## Development environment

This project uses [uv](https://docs.astral.sh/uv/) to manage Python and the virtual environment.

```sh
source .env
uv sync
uv run python --version
```

The `.env` file keeps uv's cache inside this project. Shells do not load `.env`
files automatically, so source it before using `uv` in a new terminal session.

## Whisper transcription experiment

The first executable component transcribes one recorded audio file using the
locally installed Whisper CLI and its `medium` model:

```sh
source .env
uv sync
uv run transcribe-whisper
```

That command uses the bundled 25-second sample by default. Supply a path to
transcribe a recording of your own:

```sh
uv run transcribe-whisper path/to/english-audio.wav
```

A public short sample is included for the first run:

```sh
source .env
uv run transcribe-whisper src/resources/voxtral-winning-call-8s.mp3
```

For a longer, approximately 25-second test:

```sh
source .env
uv run transcribe-whisper src/resources/voxtral-winning-call.mp3
```

The command prints only the transcript to standard output; status and errors
are written to standard error. It uses the local MacPorts model at
`/opt/local/share/whisper/models/medium.bin` by default. Set
`WHISPER_MODEL_PATH` in `.env` to use another local Whisper model.

The wrapper also supplies MacPorts' `/opt/local/lib` path when it starts
Whisper, working around a runtime-library path omission that can reappear when
the MacPorts Whisper variant is changed.

The short sample is an 8-second excerpt of the public `winning_call.mp3` file
used in Mistral's Voxtral documentation. The complete 25-second source clip is
also included as `src/resources/voxtral-winning-call.mp3`.

## Live microphone transcription

Start the local microphone process with:

```sh
source .env
uv sync
uv run transcribe-microphone
```

It captures the default microphone continuously, then sends overlapping windows
to Whisper: a 5-second window begins every 4 seconds. The one-second overlap
helps preserve words that cross a window boundary, while capture continues as
Whisper processes earlier audio. This is the current Medium Whisper baseline;
`.env` selects the locally installed `medium.bin` model. Stop it with Ctrl-C.
The expected delay is about one window plus Whisper processing time.

On first use, macOS may ask for microphone access. Grant access to the terminal
or IDE that launches the command in **System Settings → Privacy & Security →
Microphone**. For a short permission and hardware test, use:

```sh
uv run transcribe-microphone --duration 6
```

Adjust the overlap experiment with `--window-seconds` and `--stride-seconds`.
For example, 5.5-second windows every 4.5 seconds retain a one-second overlap:

```sh
uv run transcribe-microphone --window-seconds 5.5 --stride-seconds 4.5
```

If Whisper cannot keep up, the command reports a backlog warning and discards
older pending windows to remain close to live output.

### Pause-based VAD experiment

The fixed 5-second/every-4-seconds mode remains the baseline. To test local
pause-based phrase boundaries instead, add `--segmentation vad`:

```sh
uv run transcribe-microphone --segmentation vad --output-format ndjson | uv run buffer-phrases | uv run translate-stream
```

VAD keeps capture continuous, waits for approximately 0.7 seconds of silence
after speech, then sends the phrase to Whisper. It retains 0.3 seconds of
pre-roll and forces a split after 10 seconds if someone speaks without pausing.
Tune these with `--vad-silence-seconds`, `--vad-pre-roll-seconds`,
`--vad-min-phrase-seconds`, `--vad-max-phrase-seconds`, and
`--vad-aggressiveness 0` through `3`. Natural pauses improve sentence context
but add the silence threshold to live delay; omit `--segmentation vad` to return
to the fixed-window baseline.

## Streaming text translation

`translate-stream` is the next independent stage: it reads one finalized
English JSON event per line from standard input and writes the corresponding
Spanish JSON event to standard output. It uses the locally running Ollama
service and its installed `translategemma:4b` model; this project does not open
another server or port.

Start Ollama if it is not already running, then test the worker with the
narration-based fixture:

```sh
source .env
uv sync
uv run translate-stream < src/resources/translation-test-input.ndjson
```

Input events require a non-empty `text` field. `id`, `start_ms`, and `end_ms`
are optional and are retained in successful output. For example:

```json
{"id":"segment-1","text":"Good morning.","start_ms":0,"end_ms":1200}
```

Standard output contains only JSON event lines, making it safe to pipe into a
future TTS process. Status and errors are written to standard error. A malformed
input line is reported and skipped; a local Ollama/model failure produces a JSON
error event (retaining the input identifier and timing) so later input can keep
flowing.

## Live microphone to Spanish text

To run the two local stages together, use one shell pipeline:

```sh
source .env
uv run transcribe-microphone --output-format ndjson | uv run buffer-phrases | uv run translate-stream
```

This starts three focused processes. The microphone command continuously captures
audio and runs local Whisper. `buffer-phrases` combines window-bound English
text into larger translation units, then `translate-stream` passes those phrases
to local TranslateGemma. The final standard output is Spanish NDJSON, ready for
a future TTS stage. English transcripts, startup messages, and warnings remain
visible on standard error, so they do not corrupt that JSON stream.

Use Ctrl-C to stop the pipeline. The microphone event fields `start_ms` and
`end_ms` identify the approximate source Whisper window, not word-level timing.
Without `--output-format ndjson`, `transcribe-microphone` retains its original
readable-English output.

`buffer-phrases` releases text at sentence punctuation when possible. It holds
an unfinished tail for more ASR context, but flushes it after five seconds by
default so live speech cannot stall. Adjust that limit with `--max-wait-seconds`.
