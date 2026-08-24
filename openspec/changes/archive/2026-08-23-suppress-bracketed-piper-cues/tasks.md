## 1. Shared Piper sanitization

- [x] 1.1 Add a focused helper that removes complete square-bracketed cue spans and normalizes remaining whitespace while preserving unmatched brackets.
- [x] 1.2 Apply the helper in the shared `play_text` path before timing callbacks, Piper synthesis, or output-stream creation; return normally for cue-only text.

## 2. Regression coverage

- [x] 2.1 Add unit coverage for mixed spoken/cue text, cue-only text, multiple cues, and unmatched brackets.
- [x] 2.2 Run the focused speech tests and the full project test suite.
