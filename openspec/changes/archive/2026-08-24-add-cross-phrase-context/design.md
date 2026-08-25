## Context

The live pipeline finalizes short English ASR segments, buffers them into
translation-ready phrases, and translates each phrase through an independent
Ollama chat request. The paired-video evaluation showed that this isolation can
produce boundary fragments and terminology errors even when the surrounding
meaning is recoverable.

Whisper.cpp accepts an initial decoder prompt, but each current microphone
phrase starts a separate Whisper process and therefore has no retained prior
text. Ollama chat accepts an explicit message history, but the current
translator sends only one user message. Both workers must remain local,
ordered, bounded, and safe to use in a continuous live session.

## Goals / Non-Goals

**Goals:**

- Give Whisper a short, bounded prior-English hint for each later finalized
  microphone segment.
- Give TranslationGemma a bounded sequence of prior completed English/Spanish
  phrase pairs as conversational context.
- Preserve current event text and NDJSON output contracts: context guides
  inference but is never emitted as the current result.
- Make context optional, deterministic, and reset at worker/session start.

**Non-Goals:**

- No LDS glossary, retrieval system, fine-tuning, or cloud service.
- No change to VAD boundaries, phrase-buffer release policy, browser display,
  or Piper playback behavior.
- No attempt to make Whisper context a source of truth; audio remains the
  source of the current ASR result.
- No unbounded transcript or translation memory across sessions.

## Decisions

### Maintain two independent bounded histories

The ASR worker will retain only prior finalized English ASR text. The
translation worker will retain only prior successfully translated
English/Spanish phrase pairs. The histories serve different models and stages,
so sharing one buffer would introduce phrase-buffer timing and lineage
ambiguity.

The Whisper history will default to one prior finalized English segment and
the TranslationGemma history will default to two completed phrase pairs. Both
will have explicit zero-valued settings that disable context. Implementations
will also cap retained text by a small documented character/token budget so a
long phrase cannot consume the useful context window.

Alternative considered: retain the entire session transcript. Rejected because
it increases latency and prompt cost, risks stale-topic bias, and makes live
behavior progressively less predictable.

### Send Whisper context through its decoder prompt

The shared Whisper adapter will accept optional prior-English context and map
it to the CLI's `--prompt` mechanism. The prompt will contain only finalized
prior English text, and the current audio file remains the sole source of the
new transcript. Context is added after overlap reconciliation so duplicated or
discarded window text cannot bias the next call.

Alternative considered: rely on Whisper's internal rolling context. Rejected
because the application invokes a separate Whisper process for each live
phrase, so internal state does not survive between calls.

### Send TranslationGemma context as chat history

The translation worker will construct an Ollama message list consisting of a
stable translation instruction, the bounded prior English/Spanish pairs, and
the current English phrase. Previous English is represented as a user message
and its completed Spanish translation as the corresponding assistant message.
Only the response to the final current-phrase user message is emitted.

Alternative considered: concatenate prior text into the current phrase. This
would blur source text with context, make accidental retranslation more likely,
and weaken the requirement that output correspond only to the current event.

### Context updates occur only after successful finalized output

ASR history will add a segment only after it has passed overlap reconciliation
and is emitted. Translation history will add a pair only after Ollama returns a
non-empty Spanish result and that event is emitted. Failed translations,
invalid NDJSON lines, bracketed/non-speech cues, and discarded overlap text
will not become context.

Alternative considered: append input before model completion. Rejected because
an error could then poison all later translations in the live session.

### Expose context as operator controls and traceable configuration

The microphone and translation commands, plus the demo launcher where it
forwards those options, will expose context length controls. Defaults provide
the short histories above; `0` restores today's isolated behavior. Startup
diagnostics and run configuration will identify the effective settings without
logging the full private transcript history.

## Risks / Trade-offs

- [Prior text biases an ambiguous current phrase or causes a hallucinated
  continuation] → Keep histories short, make them disableable, and retain only
  finalized successful output.
- [Prompt/context length adds latency] → Cap history and compare timing traces
  with context disabled and enabled.
- [A bad translation influences later translations] → Add pairs only after a
  successful response; retain a small number of pairs and reset on worker
  start.
- [Whisper and Ollama have different context limits] → Apply stage-specific
  truncation and expose the effective limits in configuration.
- [Sensitive spoken text is exposed in diagnostics] → Report only settings and
  counts, never the retained phrase text.

## Migration Plan

1. Add the context controls with documented defaults and a `0` opt-out.
2. Verify unit tests and recorded-video evaluation with context disabled to
   preserve the current baseline.
3. Run the paired-video evaluation with the defaults and compare semantic
   review, timing, and non-speech behavior against the baseline.
4. Roll back operationally by setting both context controls to `0`; no data
   migration or persistent state cleanup is required.

## Open Questions

- The initial defaults are intentionally conservative (one ASR segment and two
  translation pairs). The recorded-video comparison should determine whether a
  larger context materially improves accuracy without increasing delay.
- A domain glossary is deferred; its eventual instructions should be added as
  separate static context rather than mixed with rolling phrase history.
