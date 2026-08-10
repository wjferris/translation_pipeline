## Why

Stopping the local browser demo with Ctrl-C can crash the Python process on macOS. The crash report shows Piper/ONNX Runtime and native audio work still active while Python is finalizing. This is a shutdown-order problem, not a translation-model failure, and must be resolved before treating the demo as a stable baseline.

## What Changes

- Make the demo coordinator retain and join its English-forwarding and Spanish speech worker threads during shutdown.
- Stop intake and child CLI processes before Python begins interpreter teardown.
- Let an in-progress Piper phrase release its native audio/ONNX resources before the demo exits.
- End browser event connections promptly during shutdown.

## Capabilities

### New Capabilities

- `demo-graceful-shutdown`: Stop the local browser demo safely when the operator presses Ctrl-C.

## Impact

- Changes only the lifecycle behavior in `demo.py`.
- Does not change the individual CLI pipeline, ASR/translation/TTS models, browser layout, or normal event order.
- Makes shutdown wait briefly for an active Spanish phrase instead of allowing Python to exit while native work is in progress.
