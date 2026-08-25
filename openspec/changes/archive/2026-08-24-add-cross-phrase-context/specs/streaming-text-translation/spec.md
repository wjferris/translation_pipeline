## ADDED Requirements

### Requirement: Condition translations with bounded completed phrase history
The system SHALL retain a bounded ordered history of successfully completed
English/Spanish phrase pairs during one `translate-stream` process and SHALL
provide the selected pairs as contextual chat history when translating the next
valid English phrase. It SHALL emit only the Spanish translation of the current
input event.

#### Scenario: Translate a phrase after a prior successful translation
- **WHEN** `translate-stream` receives a valid current English phrase after it
  has emitted one or more successful Spanish translations with context enabled
- **THEN** it SHALL send the selected prior English/Spanish pairs and the
  current English phrase to the local Ollama chat model
- **AND** it SHALL emit one Spanish NDJSON event for the current phrase only

#### Scenario: Start a fresh translation worker
- **WHEN** `translate-stream` starts a new process
- **THEN** it SHALL begin with an empty completed-phrase history and SHALL send
  its first valid phrase without prior translation pairs

#### Scenario: Disable translation phrase context
- **WHEN** an operator sets the translation context length to `0`
- **THEN** `translate-stream` SHALL omit prior phrase pairs from the model
  request and SHALL otherwise preserve the existing stream-safe output
  behavior

#### Scenario: Exclude unsuccessful work from context
- **WHEN** an input line is invalid or a translation request fails or returns
  no Spanish text
- **THEN** the system SHALL not add that input or error result to the completed
  phrase history used by later translations
