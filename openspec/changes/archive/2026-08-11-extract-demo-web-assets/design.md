## Context

`demo.py` currently owns browser serving, pipeline coordination, and the full HTML/CSS/JavaScript page as one Python string. The local demo is intentionally lightweight and offline, so separating static files should not add a frontend framework, dependency manager, or build process.

## Decisions

### Use plain static files under project resources

Store `index.html`, `demo.css`, and `demo.js` under `src/resources/web/`. They remain directly readable and editable with any text editor. The existing Babel-fish image stays in `src/resources/images/`.

### Keep a fixed local asset allow-list

The Python handler serves only the known page, stylesheet, script, and favicon paths. It does not expose arbitrary project files or create network-facing static hosting.

### Preserve browser behavior

The page continues to open from `127.0.0.1`, subscribe to `/events`, display bounded English/Spanish history, and use the same visual design. The Python coordinator and CLI pipeline are otherwise unchanged.

## Risks and Rollback

- [A missing asset breaks page styling or updates] → Serve clear 404 responses and smoke-test each asset.
- [Static serving exposes local files] → Use fixed URL-to-file mappings only.
- [Refactor affects the display] → Restore the previous commit; the refactor does not alter ASR, translation, or Piper behavior.
