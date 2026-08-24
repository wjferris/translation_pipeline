## Why

The live translation pipeline is functional, but its code-level responsibilities and runtime message flow are spread across several modules and worker threads. A focused visual evaluation will make the current abstractions, ownership boundaries, and event sequence easier to understand before considering any refactoring.

## What Changes

- Add a documentation-only evaluation of the existing live translation implementation.
- Create a code/class diagram showing the principal classes, functions, and relationships involved in the pipeline.
- Create a sequence diagram showing microphone capture through transcription, phrase buffering, translation, browser events, and speech output.
- Convert the README's current local-demo Mermaid architecture diagram to editable PlantUML and SVG evaluation artifacts.
- Use the installed `plantuml` skill to create, validate, and retain the editable diagram sources.
- Render both diagrams as SVG files in a new repository-level `evaluation/` folder.
- Do not modify application behavior, APIs, or runtime abstractions.

## Capabilities

### New Capabilities

- `code-architecture-evaluation`: Documents existing implementation structure, runtime collaboration, and README-level local-demo architecture through editable PlantUML and SVG diagrams.

### Modified Capabilities

<!-- No product or runtime requirements change. -->

## Impact

- Adds evaluation artifacts under `evaluation/` and the corresponding OpenSpec change documentation.
- Uses the installed `plantuml` skill and the repository SVG-rendering workflow; no new application dependency is required.
- Reads the existing Python modules, browser assets, and tests to build an accurate current-state model.
- No production dependencies, public interfaces, or executable behavior are changed.
