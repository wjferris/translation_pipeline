## 1. Baseline and test material

- [ ] 1.1 Record or collect representative direct-feed examples of podium speech, competing audience speech, and cough/sneeze or other transient noise.
- [ ] 1.2 Capture the direct-feed baseline: audio quality, ASR transcript observations, VAD behavior, and end-to-end latency.
- [ ] 1.3 Define acceptance thresholds for desired-speech preservation, false transcripts, added latency, CPU use, and recovery after device changes.

## 2. Candidate assessment

- [ ] 2.1 Research local-only, macOS-compatible open-source enhancement options and their physical-input to selectable-virtual-input routing model.
- [ ] 2.2 Identify whether each candidate performs ordinary noise suppression, competing-voice suppression, or both, and document its expected limitations with a single podium microphone.
- [ ] 2.3 Reject candidates that require cloud audio processing, conferencing-only integration, or an unreliable/unsupported virtual-device chain.

## 3. Controlled evaluation and decision

- [ ] 3.1 Run each viable candidate against the common test material and compare speech preservation, suppression, ASR transcripts, VAD behavior, latency, and CPU use with the direct feed.
- [ ] 3.2 Test candidate startup, stop, physical-input reconnect, and direct-feed fallback behavior on macOS.
- [ ] 3.3 Record a recommend, defer, or reject decision with evidence; create a separate implementation change only if a candidate meets the acceptance thresholds.
