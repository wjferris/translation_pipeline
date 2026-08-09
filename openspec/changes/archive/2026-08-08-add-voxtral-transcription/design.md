## Context

The project currently contains only the Python environment and project documentation. The first executable experiment must accept recorded English audio and expose Voxtral's raw transcription result before translation, speech synthesis, streaming, or AV integration are considered. The developer is starting on macOS, while later deployment is expected to use Linux and NVIDIA hardware.

## Goals / Non-Goals

**Goals:**

- Provide one command that transcribes a local audio file and writes only the transcript to standard output.
- Use Mistral's locally downloadable Voxtral Mini model through the supported Transformers interface.
- Select available hardware automatically, preferring CUDA, then Apple Silicon MPS, then CPU.
- Make expected model download and hardware limitations clear in the README.

**Non-Goals:**

- Live audio capture, streaming, translation, text-to-speech, captions, speaker diarization, glossary support, and OBS/Zoom integration.
- Providing an optimized server or guaranteeing real-time performance on CPU or older hardware.

## Decisions

### Use Voxtral Mini with Transformers

The script will use `mistralai/Voxtral-Mini-3B-2507`, `VoxtralForConditionalGeneration`, and `AutoProcessor` through Transformers' dedicated transcription request API. This follows Mistral's published local example and avoids introducing a vLLM service for a single-file proof of concept.

`librosa` is declared explicitly because Transformers' local audio loader requires it for the file-based transcription request.

Alternative: run vLLM. Mistral recommends it for serving, but it introduces a separate service and is better evaluated when the project reaches streaming or multi-client operation.

### Expose a small package command

The implementation will provide `uv run transcribe-voxtral path/to/audio.wav`. The command will validate its argument, load the model on first use, generate an English transcript with deterministic transcription settings, and print the transcript as its only standard-output payload.

Alternative: a notebook or a one-off shell command. A package command is easier to repeat, document, and carry forward to Linux.

### Choose the device automatically

CUDA is preferred when available; otherwise MPS is used on Apple Silicon, then CPU. The chosen device is reported to standard error so standard output stays suitable for piping into the future translation step.

### Include a short example clip

The project will include an 8-second excerpt of the public `winning_call.mp3`
sample referenced by Mistral's Voxtral documentation. A known short clip lets a
new developer test the command without locating or sharing a meeting recording.

### Default to cached model files

Both processor and model loads will set `local_files_only=True` by default, so
normal transcription does not make Hugging Face requests. An explicit
`--download` flag will opt into Hub access when a user needs to bootstrap or
refresh the local cache. If cached files are absent during an offline run, the
error will tell the user to rerun with `--download`.

## Risks / Trade-offs

- [Voxtral Mini's weights are large and the initial download is substantial] → Document the download and make first execution an explicit, recorded-audio experiment.
- [MPS or CPU performance may be unsuitable for long audio] → Keep this change offline-only and collect timing observations before choosing deployment hardware.
- [Audio codec support varies by local installation] → Validate the given path and surface model/library errors without attempting implicit conversion in this first change.
- [A local cache might not yet contain every model file] → Fail with an explicit instruction to rerun once with `--download`.
