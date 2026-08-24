## Context

The current implementation is a local, process-oriented live translation pipeline. `demo.py` owns the browser-facing coordinator and event stream, while microphone capture, segmentation, transcription, phrase buffering, translation, and speech playback are distributed across modules and subprocess boundaries. The evaluation must describe this current state without proposing or applying a refactor.

## Goals / Non-Goals

**Goals:**

- Produce a focused code/class view of the principal implementation objects and their relationships.
- Produce a sequence view of the main live-demo flow, including subprocesses, worker threads, browser events, translation, and speech playback.
- Preserve the README's higher-level local-demo architecture as editable PlantUML and SVG.
- Render both diagrams as readable SVG files under `evaluation/`.
- Make the diagrams traceable to the current source files and clearly label process or thread boundaries.

**Non-Goals:**

- Changing production Python, browser assets, dependencies, or runtime behavior.
- Introducing a new abstraction layer or recommending a target architecture as part of this change.
- Exhaustively documenting every helper function, error branch, or CLI option.

## Decisions

- **Use current-state structural and behavioral views.** The code/class diagram will focus on `DemoPipeline`, `DemoState`, `DemoHandler`, `DemoHTTPServer`, the audio segmenters, `PhraseBuffer`, and the translation/speech functions. The sequence diagram will follow the normal `demo.py` startup and event path. This keeps the evaluation useful for identifying unclear ownership without turning it into a redesign.
- **Use PlantUML as the editable source and SVG as the rendered format.** PlantUML provides suitable class and sequence notation, while SVG preserves searchable text and scales cleanly. Each `.puml` source will be retained beside its rendered SVG in `evaluation/` so future evaluations can regenerate or revise the diagrams.
- **Use the installed `plantuml` skill as the generation workflow.** The implementation will follow its type-specific class and sequence guidance, create and validate `.puml` sources, and use the repository's SVG renderer to preserve required metadata. This provides repeatable UML notation and local rendering without sending source code to an external service.
- **Use three narrowly scoped diagrams.** A single combined diagram would be difficult to read. The code/class diagram explains implementation structure; the sequence diagram explains runtime ordering and concurrency; the converted README diagram preserves the higher-level local-demo architecture already documented for readers.
- **Treat the README Mermaid diagram as source material, not a replacement target.** Its nodes, VAD decision branches, data-flow labels, local-only boundary, and visual grouping will be translated into PlantUML equivalents in `evaluation/`. The README Mermaid source remains unchanged so this evaluation does not alter existing documentation behavior.
- **Annotate evidence with source file names.** Diagram labels and accompanying captions will identify the relevant modules, so readers can distinguish observed implementation relationships from inferred conceptual groupings.
- **Include SVG metadata.** Each SVG will include title, creator, and rights metadata so the generated artifacts are self-describing.

## Risks / Trade-offs

- [Risk] The implementation has both direct function calls and subprocess CLI stages, which can make one diagram appear more tightly coupled than the other. → Mitigation: show process boundaries explicitly and use distinct relationship labels for calls, pipes, and published browser events.
- [Risk] A code-level diagram can become too dense. → Mitigation: include only principal classes, functions, and data types involved in the live-demo path; omit routine argument parsing and low-level helpers.
- [Risk] The diagrams can become stale as the implementation changes. → Mitigation: label the evaluation as a current-state snapshot and keep the source references close to the generated artifacts in the change documentation.
