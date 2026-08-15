## Context

The live POC receives a direct wireless feed of the podium microphone through
an RCA-connected interface. That physical path should reduce room ambience, but
does not guarantee that audience voices, coughing, or transient noises will be
absent. The current local VAD choices classify speech activity; neither proves
that it can identify the intended speaker.

The project must preserve local-only processing, intelligible podium speech,
and near-live latency. It has not selected a macOS virtual microphone, audio
enhancement library, hardware DSP, or source of truth for the input device.

## Goals / Non-Goals

**Goals:**

- Compare the unprocessed direct feed with candidate local pre-ASR enhancement
  paths using representative clean speech, audience speech, and transient noise.
- Assess suppression, desired-speech preservation, added latency, stability,
  CPU use, and macOS routing compatibility.
- Produce a documented recommend/defer/reject decision before a later
  implementation change.

**Non-Goals:**

- Installing software, adding a virtual input device, or changing the Sunday
  POC configuration.
- Claiming that a single microphone can deterministically identify the podium
  speaker.
- Replacing the existing WebRTC or Silero VAD backend, changing translation, or
  adding cloud audio processing.

## Decisions

### Evaluate speaker isolation separately from VAD

Candidate processing is a pre-ASR audio enhancement stage. It is not a new VAD
backend: VAD decides when speech is present, whereas enhancement attempts to
improve the audio before VAD and ASR. This preserves a clear A/B boundary and
allows the existing Silero result to remain the baseline.

### Use a three-class test set and direct-feed baseline

Every candidate must be compared against the same direct feed with (1) podium
speech, (2) competing audience speech, and (3) cough/sneeze/ambient transient
samples. A clean direct feed is the control. Subjective intelligibility and
transcript error review are primary; generic denoiser marketing claims are not
sufficient evidence.

### Treat virtual audio routing as a first-class compatibility test

Any software candidate must expose a stable selectable macOS input that can
receive a physical RCA/USB interface and be consumed by the Python capture
path. A candidate that requires cloud processing, a conferencing-only app
integration, or an unsupported virtual-device chain is rejected for this POC.

### Prefer reversible, optional integration

If later adopted, the enhancement stage will be an opt-in input path with the
direct feed retained as the immediate fallback. This avoids introducing a
single point of failure before a live event.

## Risks / Trade-offs

- [Suppression removes quiet podium syllables or alters names] → Compare ASR
  transcripts and audio before/after; reject candidates that harm speech.
- [Added latency makes translation feel delayed] → Measure end-to-end timing
  against the direct-feed baseline and set an acceptance threshold before
  implementation.
- [Audience voice is too similar to podium speech] → Record this limitation;
  prefer microphone placement/source routing over a false isolation claim.
- [Virtual-device instability] → Test start/stop, source reconnect, and device
  selection; retain direct input as the rollback path.

## Migration Plan

This exploration creates no runtime migration. A later approved implementation
will add an optional input route, document the selected physical source and
virtual device, and provide a direct-feed fallback command.

## Open Questions

- Is audience speech materially present in the direct podium feed during a
  regular meeting?
- Does a local open-source enhancement path meet real-time latency and macOS
  device-routing requirements without excessive operational complexity?
- What degree of ASR improvement justifies an additional live-audio component?
