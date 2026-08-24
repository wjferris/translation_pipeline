## 1. Source inspection

- [x] 1.1 Trace the live-demo coordinator, HTTP/SSE handler, and browser asset loading in `demo.py`.
- [x] 1.2 Trace microphone capture, segmenter selection, Whisper execution, phrase buffering, translation, and Piper playback.
- [x] 1.3 Record the source-file evidence and boundary types needed to distinguish calls, pipes, threads, subprocesses, and SSE.

## 2. Diagram generation

- [x] 2.1 Use the installed `plantuml` skill's class-diagram guidance to create and validate a source scoped to the principal current-state classes, functions, and data objects.
- [x] 2.2 Use the installed `plantuml` skill's sequence-diagram guidance to create and validate a source for the normal live-demo event flow and its concurrency boundaries.
- [x] 2.3 Render both locally validated diagrams to SVG with the repository diagram metadata requirements.
- [x] 2.4 Place each editable `.puml` source beside its final SVG at `evaluation/`.

## 3. Verification

- [x] 3.1 Validate both outputs as well-formed SVG documents.
- [x] 3.2 Inspect the rendered SVGs for readable labels, complete boundaries, and no clipped content.
- [x] 3.3 Confirm no production code, browser assets, dependencies, or runtime behavior changed.

## 4. README Mermaid conversion

- [x] 4.1 Map the README Mermaid nodes, VAD decision branches, data-flow labels, and local-Mac boundary to PlantUML equivalents.
- [x] 4.2 Use the installed `plantuml` skill to create and locally validate `evaluation/readme-local-demo-architecture.puml`.
- [x] 4.3 Render and visually inspect `evaluation/readme-local-demo-architecture.svg` with required SVG metadata, confirming the README source remains unchanged.
