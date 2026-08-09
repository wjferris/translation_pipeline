## 1. Phrase-buffer worker

- [x] 1.1 Add the `buffer-phrases` console command and NDJSON stream handling.
- [x] 1.2 Implement punctuation-boundary phrase release, timing/source metadata, timeout flush, and end-of-input flush.
- [x] 1.3 Remove only obvious one-word overlap duplicates at an ASR event boundary.

## 2. Pipeline documentation and verification

- [x] 2.1 Update the documented live pipeline to include `buffer-phrases` and explain the added bounded delay.
- [x] 2.2 Verify sentence-boundary, timeout, end-of-input, and overlap-deduplication behavior using local NDJSON input.
- [x] 2.3 Verify phrase output is accepted by `translate-stream`.

## 3. OpenSpec verification

- [x] 3.1 Validate the completed OpenSpec change artifacts.
