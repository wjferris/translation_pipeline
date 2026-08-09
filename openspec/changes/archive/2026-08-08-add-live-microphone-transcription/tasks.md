## 1. Microphone capture foundation

- [x] 1.1 Select and add a minimal local microphone-capture dependency.
- [x] 1.2 Implement a long-running default-microphone capture command with configurable chunk duration and clean Ctrl-C shutdown.

## 2. Local transcription loop

- [x] 2.1 Reuse the local Whisper wrapper to transcribe each captured chunk and print completed text lines.
- [x] 2.2 Report microphone permission, device, and transcription failures clearly on standard error.
- [x] 2.3 Suppress recurring Whisper model-status output during live transcription.

## 3. Documentation and verification

- [x] 3.1 Document macOS microphone permission, expected chunking delay, usage, and stopping behavior.
- [x] 3.2 Verify the command help and, with user-authorized microphone access, a short end-to-end live transcription run.
- [x] 3.3 Validate the OpenSpec change artifacts.
