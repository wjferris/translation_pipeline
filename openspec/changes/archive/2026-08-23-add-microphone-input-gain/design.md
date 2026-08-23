## Context

`transcribe-microphone` captures the default Core Audio device as 16 kHz, mono `float32` blocks. Those blocks enter a shared queue before either fixed-window segmentation, WebRTC VAD, or Silero VAD. Some USB line-input adapters report a fixed 0 dB input level to macOS, leaving no operating-system control to raise a quiet but valid source.

## Goals / Non-Goals

**Goals:**

- Provide a documented `--input-gain-db` command-line setting with a default of 0 dB.
- Apply the requested gain once, immediately after capture and before every downstream segmenter and transcription path.
- Keep emitted sample values in the valid normalized `float32` range and report the configured gain at startup.
- Reject impractical configuration values before microphone capture begins.

**Non-Goals:**

- Selecting an input device or changing its macOS/hardware gain.
- Automatic gain control, normalization, compression, noise reduction, or a live level meter.
- Altering Whisper, Piper, translation, or browser-display behavior.

## Decisions

### Apply gain in the shared capture callback

The callback will multiply each captured block by `10 ** (input_gain_db / 20)` before queueing it, then clip it to `[-1.0, 1.0]`. This makes gain behavior identical for fixed windows and both VAD backends, and means VAD receives the same amplified signal that Whisper receives.

Applying gain only when writing WAV files was considered, but would leave VAD thresholds operating on the quiet original signal. Applying it independently inside each segmenter would duplicate logic and risk behavior differences.

### Expose a bounded decibel option

`--input-gain-db` will accept a floating-point value from -48 dB through +48 dB, inclusive, and default to `0`. The range covers common attenuation and quiet line-input compensation (including the roughly +30 dB needed for a 0.001 peak) while preventing accidental extreme amplification.

An unbounded option was considered but would make a typo capable of producing unusable, permanently clipped segments. Hardware gain control is not used because the affected adapters do not expose it to macOS.

### Preserve validity by clipping, and surface the setting

Clipping protects the normalized audio contract used by `soundfile`, VAD libraries, and Whisper. Startup status written to standard error will include the selected gain in dB so capture logs identify the effective configuration. Clipping is preferable to allowing out-of-range samples, which can produce invalid or implementation-dependent audio.

## Risks / Trade-offs

- [Gain raises ambient noise along with speech] → Keep the zero-gain default and require an explicit operator choice.
- [High gain clips loud input] → Clip safely to the supported range and document that operators should lower gain when audio distorts.
- [Gain changes VAD sensitivity] → Apply it before VAD intentionally; users can tune existing VAD controls if their noise floor changes.
- [The hardware source is disconnected or too weak] → Gain improves a valid quiet signal but cannot repair a cable, source, or adapter fault.

## Migration Plan

Existing commands continue to use `0 dB` by default. Operators with fixed-gain line adapters can opt in with, for example, `--input-gain-db 30`; rollback is removing the option or setting it to `0`.

## Open Questions

None.
