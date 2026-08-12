## ADDED Requirements

### Requirement: Recognizable BabelFish demo process hierarchy

The demo mode SHALL identify its coordinator and demo-launched worker roles as BabelFish processes in local process listings where supported by the operating system.

#### Scenario: Inspect a running demo

- **WHEN** an operator starts the local demo and inspects its local process tree
- **THEN** the coordinator is distinguishable as the BabelFish demo
- **AND** the demo-launched ASR and phrase-buffer roles are distinguishable from unrelated Python processes where platform process titles permit.

### Requirement: Common demo lifecycle group

The demo coordinator and its demo-launched child processes SHALL belong to an isolated local session and process group with an inspectable lifecycle relationship. The normal demo launcher SHALL return after starting that background session and SHALL record the session leader PID for a companion stop command.

#### Scenario: Stop a running demo

- **WHEN** the operator stops demo mode
- **THEN** the companion stop command sends a graceful interrupt to the isolated demo process group
- **AND** the existing graceful Piper shutdown behavior remains in effect.

#### Scenario: Start and stop from launcher commands

- **WHEN** an operator runs `scripts/run-demo`
- **THEN** the command starts the isolated BabelFish demo session in the background and returns control to the shell
- **WHEN** the operator runs `scripts/stop-demo`
- **THEN** the system requests graceful shutdown of that demo session without signalling the operator's shell.

### Requirement: Preserve standalone CLI operation

The process identity feature SHALL NOT change the independently runnable CLI commands outside demo mode.

#### Scenario: Run a CLI worker directly

- **WHEN** an operator runs `transcribe-microphone` or `buffer-phrases` directly
- **THEN** it operates without requiring the BabelFish demo process group.
