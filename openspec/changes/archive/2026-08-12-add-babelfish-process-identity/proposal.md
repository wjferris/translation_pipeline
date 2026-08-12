## Why

The local demo is intentionally composed of a coordinator and focused worker processes. In Activity Monitor and terminal process listings, however, they currently appear as generic Python commands. A recognizable BabelFish process tree would make live-operation troubleshooting and safe shutdown easier.

## What Changes

- Give the demo coordinator and its child workers recognizable BabelFish role names where the operating system supports process titles.
- Start all demo subprocesses in a common process group/session owned by the BabelFish demo launcher.
- Report the process identity/group to the operator at startup when useful.
- Start the demo in the background through the launcher and provide a companion command that safely stops its isolated process group.

## Capabilities

### New Capabilities

- `babelfish-process-identity`: Present the local demo and its child workers as a recognizable, controllable BabelFish process group.

## Impact

- Affects only demo process startup, visibility, and shutdown coordination.
- Does not change the browser UI, ASR, translation, Piper playback, NDJSON protocol, or CLI-only commands.
- May add a small local process-title helper dependency if a reliable macOS-compatible approach is selected.
