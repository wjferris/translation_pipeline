## ADDED Requirements

### Requirement: Configure local microphone input gain
The system SHALL allow `transcribe-microphone` callers to set `--input-gain-db` as a floating-point gain from -48 dB through +48 dB, inclusive. The option SHALL default to `0 dB`. Before the system queues each captured normalized microphone block for fixed-window or VAD segmentation, it SHALL multiply the block by the linear factor `10 ** (input_gain_db / 20)` and clip every output sample to the inclusive range `[-1.0, 1.0]`. The system SHALL write the selected input gain to standard error in its startup status.

#### Scenario: Use the default zero-gain capture path
- **WHEN** a user starts `transcribe-microphone` without `--input-gain-db`
- **THEN** the system SHALL queue the captured samples unchanged by gain multiplication and report `0 dB` input gain at startup

#### Scenario: Amplify a quiet line input
- **WHEN** a user starts `transcribe-microphone --input-gain-db 30`
- **THEN** the system SHALL multiply every captured sample by the linear factor for +30 dB before fixed-window or VAD segmentation and report `+30 dB` input gain at startup

#### Scenario: Prevent amplified samples from exceeding the audio range
- **WHEN** a configured gain would produce a sample greater than `1.0` or less than `-1.0`
- **THEN** the system SHALL queue that sample as `1.0` or `-1.0`, respectively

#### Scenario: Reject an unsupported input gain
- **WHEN** a user supplies `--input-gain-db` outside -48 dB through +48 dB
- **THEN** the command SHALL exit with status 2 before opening the microphone and write an actionable validation error to standard error
