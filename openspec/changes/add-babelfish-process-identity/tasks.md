## 1. Process identity design validation

- [ ] 1.1 Evaluate a macOS-compatible method for setting useful parent and child process titles.
- [ ] 1.2 Select and document the process-group/session mechanism for demo-launched children.

## 2. Demo lifecycle implementation

- [ ] 2.1 Add BabelFish identity to the demo coordinator and role-specific identity to its child workers.
- [ ] 2.2 Establish the shared process lifecycle boundary without affecting standalone CLI workers.
- [ ] 2.3 Add operator-facing startup diagnostics for the relevant process identity or group.

## 3. Validation and documentation

- [ ] 3.1 Verify process visibility with `ps` and Activity Monitor on macOS.
- [ ] 3.2 Verify graceful Ctrl-C shutdown leaves no BabelFish child workers behind.
- [ ] 3.3 Document the process tree and troubleshooting commands.
