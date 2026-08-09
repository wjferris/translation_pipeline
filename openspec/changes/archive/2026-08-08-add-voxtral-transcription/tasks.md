## 1. Voxtral transcription command

- [x] 1.1 Add the Transformers, Torch, and audio-processing dependencies required by Voxtral Mini.
- [x] 1.2 Implement the `transcribe-voxtral` command with argument validation and automatic device selection.
- [x] 1.3 Load the Voxtral Mini transcription model and print only the English transcript to standard output.
- [x] 1.4 Add and verify the audio-decoding dependency required by the local file input path.
- [x] 1.5 Make cached local model loading the default and provide an explicit download option.

## 2. Documentation and verification

- [x] 2.1 Document the command, initial model download, and hardware expectations in the README.
- [x] 2.2 Verify the command's help and missing-file behavior without downloading model weights.
- [x] 2.3 Validate the OpenSpec change artifacts.
- [x] 2.4 Verify that normal loading receives the local-only setting without downloading model weights.

## 3. Repeatable sample input

- [x] 3.1 Add a public 5-10 second audio sample under `src/resources/` and document its transcription command.
