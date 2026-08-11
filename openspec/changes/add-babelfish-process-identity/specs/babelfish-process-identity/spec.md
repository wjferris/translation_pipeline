## ADDED Requirements

### Requirement: Recognizable BabelFish demo process hierarchy

The demo mode SHALL identify its coordinator and demo-launched worker roles as BabelFish processes in local process listings where supported by the operating system.

#### Scenario: Inspect a running demo

- **WHEN** an operator starts the local demo and inspects its local process tree
- **THEN** the coordinator is distinguishable as the BabelFish demo
- **AND** the demo-launched ASR and phrase-buffer roles are distinguishable from unrelated Python processes where platform process titles permit.

### Requirement: Common demo lifecycle group

The demo coordinator and its demo-launched child processes SHALL belong to a common local process group or session with an inspectable lifecycle relationship.

#### Scenario: Stop a running demo

- **WHEN** the operator stops demo mode
- **THEN** the common lifecycle relationship assists cleanup of its child workers
- **AND** the existing graceful Piper shutdown behavior remains in effect.

### Requirement: Preserve standalone CLI operation

The process identity feature SHALL NOT change the independently runnable CLI commands outside demo mode.

#### Scenario: Run a CLI worker directly

- **WHEN** an operator runs `transcribe-microphone` or `buffer-phrases` directly
- **THEN** it operates without requiring the BabelFish demo process group.
