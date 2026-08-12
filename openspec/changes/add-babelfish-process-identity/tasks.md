## 1. Process identity design validation

- [x] 1.1 Evaluate a macOS-compatible method for setting useful parent and child process titles.
- [x] 1.2 Select and document the process-group/session mechanism for demo-launched children.

## 2. Demo lifecycle implementation

- [x] 2.1 Add BabelFish identity to the demo coordinator and role-specific identity to its child workers.
- [x] 2.2 Establish an isolated shared process lifecycle boundary without affecting standalone CLI workers.
- [x] 2.3 Add background-launch and stop-command diagnostics for the relevant process identity or group.

## 3. Validation and documentation

- [x] 3.1 Verify process visibility and shared process-group identity with `ps` on macOS (Activity Monitor is best effort).
- [x] 3.2 Verify the stop command leaves no BabelFish child workers behind after graceful shutdown.
- [x] 3.3 Document the process tree and troubleshooting commands.
