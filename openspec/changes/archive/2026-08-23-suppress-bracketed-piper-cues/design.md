## Context

Translated text reaches Piper through the shared `play_text` function.  Non-speech annotations such as `[blank audio]` are valid text to the current implementation, so Piper speaks them in both `speak-stream` and the browser demo.

## Goals / Non-Goals

**Goals:**

- Remove complete square-bracketed cue annotations immediately before local Piper synthesis.
- Preserve the surrounding spoken text and its playback order.
- Skip synthesis and audio-device setup when a value contains only cues or whitespace.

**Non-Goals:**

- Change transcription, translation, browser display, event contents, or timing-trace records.
- Interpret non-bracketed text as a cue or alter Piper model/device selection.

## Decisions

### Sanitize at the shared playback boundary

`play_text` will remove complete non-nested square-bracketed spans and normalize the resulting whitespace before it invokes `voice.synthesize`. This protects every current caller without altering displayed or persisted translation text. Sanitizing upstream was rejected because the browser and trace should retain the original translation evidence.

### Treat cue-only input as successful no playback

If sanitization leaves no non-whitespace text, `play_text` will return before invoking Piper or opening an output stream. This preserves sequencing while avoiding an audible placeholder and avoids reporting an error for a normal annotation.

### Keep unmatched brackets as spoken content

Only complete `[...]` spans are removed. An unmatched bracket remains in text so a malformed translation does not silently lose spoken content. Nested brackets are outside the expected cue format and follow the same complete-span behavior.

## Risks / Trade-offs

- [A legitimate phrase inside brackets is suppressed] → The requested bracket convention reserves complete bracketed spans for non-speech annotations at the Piper boundary.
- [Whitespace changes around a removed cue] → Collapse it to one space so remaining speech is natural and punctuation is retained.

## Migration Plan

No migration is required. New invocations immediately sanitize only the text supplied to Piper. Removing the sanitizer restores prior behavior without changing saved events.

## Open Questions

None.
