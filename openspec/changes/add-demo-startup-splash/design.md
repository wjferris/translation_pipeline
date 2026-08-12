## Context

The loopback-only `demo` command starts local speech recognition, Ollama translation, Piper speech, and a browser display. The display's HTML, CSS, and JavaScript are independently editable web assets, while `demo.py` owns local HTTP routes and the selected translation model. The page currently renders the transcript view immediately and only receives live status through server-sent events.

## Goals / Non-Goals

**Goals:**

- Give the audience a polished 5–7 second startup screen before the transcript view is revealed.
- Identify the selected translation model and report locally discoverable Ollama/runtime version information.
- Keep startup entirely local and avoid delaying or blocking the demo if optional metadata cannot be read.
- Keep the browser interaction and accessibility state unambiguous while the splash is active.

**Non-Goals:**

- No new remote service, authentication, telemetry, or browser persistence.
- No guarantee that every Ollama installation can expose a model build/digest; unavailable values are reported as unavailable.
- No replacement of the existing terminal validation, event stream, or normal run commands.

## Decisions

### Serve a small startup-information payload from the local coordinator

The coordinator will expose a loopback-only JSON route containing the selected translation-model identifier and best-effort local version metadata. It will obtain the Ollama server version using the installed client/API where supported and match the configured model against locally available model metadata to expose an identifying version/tag or digest. It will also include the Python package/application version when readily available.

This preserves a single source of truth for command-line settings and avoids making the browser connect directly to Ollama. Metadata lookup is bounded and failure-tolerant so unavailable or older Ollama installations result in a labeled unavailable field rather than a failed demo. Embedding version values into HTML was considered, but a JSON route keeps the static web assets editable and permits a clear loading state.

### Use a six-second default, client-side splash timer

The static page will include an initially visible full-screen splash overlay. JavaScript will populate it from the startup-information route, show loading/readiness text, and remove or conceal it after six seconds—inside the requested 5–7 second window. Live transcript events may be collected during the overlay but the bilingual display will only become visible when the timer completes.

A server-side delay was considered but rejected because it would defer opening a responsive page and make browser rendering dependent on worker timing. A fixed six-second client timer gives consistent presentation timing while the coordinator continues starting local workers.

### Make the overlay a presentation layer rather than a second page

The splash will live in the existing index, styled above the normal header and transcript panes, then transition away cleanly. It will present the product name, loading status, and a readable metadata list with an explicit unavailable state. The underlying demo remains accessible in the DOM and resumes its existing status/event handling after the overlay clears.

A separate splash route was considered but rejected because it complicates navigation, event setup, and returning to the live page.

## Risks / Trade-offs

- [Ollama is down, old, or returns incomplete model metadata] → Bound the lookup, return stable unavailable values, and continue startup.
- [Metadata lookup adds startup latency] → Perform it independently of the fixed browser timer and avoid adding it to critical worker validation.
- [A screen reader sees both splash and transcript content] → Apply appropriate overlay semantics and hide or mark the underlying presentation state during startup.
- [Early transcript events arrive during the splash] → Retain existing client history so the page reveals the most recent configured lines once active.

## Migration Plan

The change is additive to the local demo assets and loopback HTTP API. Deploy with the normal application update; rollback consists of reverting the new route and overlay assets, returning the immediate transcript display. No persisted data or external configuration migration is required.

## Open Questions

- None; the implementation will use the selected model tag as the model-version display when Ollama cannot provide a more specific local digest or detail.
