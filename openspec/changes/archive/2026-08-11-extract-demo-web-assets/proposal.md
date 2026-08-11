## Why

The demo page's HTML, CSS, and browser event code are embedded in `demo.py`. This makes ordinary presentation changes unnecessarily risky and difficult to review alongside Python process logic.

## What Changes

- Move the local demo page markup, stylesheet, and browser JavaScript into separately editable files under `src/resources/web/`.
- Have the existing loopback Python server serve those known local assets.
- Keep the existing event endpoint, visual behavior, and fully local operation unchanged.

## Capabilities

### New Capabilities

- `editable-demo-web-assets`: Maintain the local demo UI as independently editable HTML, CSS, and JavaScript assets.

## Impact

- Simplifies future visual/UI changes without introducing a web framework or a Node build step.
- Limits the Python server to serving a fixed allow-list of local assets and the existing event stream.
