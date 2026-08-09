## 1. Continuous capture foundation

- [x] 1.1 Replace sequential microphone recording with continuous callback-based capture and a bounded window queue.
- [x] 1.2 Add configurable window duration, stride, and backlog warning settings with 6-second/5-second defaults.

## 2. Overlapped transcription

- [x] 2.1 Process queued windows in a worker while capture continues.
- [x] 2.2 Implement conservative word-overlap de-duplication for displayed transcript text.
- [x] 2.3 Make Ctrl-C terminate active Whisper work and clean up threads and temporary files reliably.

## 3. Verification and documentation

- [x] 3.1 Document window/stride settings, expected delay, overlap behavior, and backlog warnings.
- [x] 3.2 Verify continuous capture, overlap output, and interruption behavior with a short microphone trial.
- [x] 3.3 Validate the OpenSpec change artifacts.
