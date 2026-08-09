## 1. Pending-window reconciliation

- [x] 1.1 Create a timestamped, project-local pre-change snapshot of `buffer_phrases.py` and relevant README text, with a `RESTORE.md` containing exact restoration commands.
- [ ] 1.2 Refactor `buffer-phrases` to retain one pending ASR event before phrase commitment.
- [ ] 1.3 Implement normalized multiword adjacent-window alignment, including punctuation/case normalization and hyphenated word components.
- [ ] 1.4 Apply successor wording within a recognized overlap and carry combined source IDs/timing into the phrase buffer.

## 2. Bounded live behavior

- [ ] 2.1 Preserve sentence-boundary release while committing only reconciled stable text.
- [ ] 2.2 Flush pending and unfinished text on timeout and end of input without blocking later events.
- [ ] 2.3 Document the added one-window latency and unchanged shell pipeline.
- [x] 2.4 Test the changed pipeline with a controlled reading; restore the snapshot if it regresses duplication, omissions, or acceptable latency.

## 3. Verification

- [ ] 3.1 Add focused local NDJSON tests for exact, punctuation/case, and hyphenated overlap cases plus non-overlap safety.
- [ ] 3.2 Verify reconciled phrase output remains accepted by `translate-stream`.
- [ ] 3.3 Validate the completed OpenSpec change artifacts.

## 4. Rejected experiment

- [x] 4.1 Restore the pre-change snapshot after the controlled reading showed no material improvement in duplication or translation quality.
