## Why

The continuous-capture experiment showed a promising lower-latency baseline using the locally installed Small Whisper model with shorter overlapping windows. The project defaults still describe the earlier 6-second window every 5 seconds, which makes routine testing slower than intended.

## What Changes

- Change the default live microphone window from 6 seconds every 5 seconds to 4 seconds every 3 seconds.
- Document the 4-second/3-second baseline and confirm that `.env` already selects the locally installed Small Whisper model.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `live-microphone-transcription`: Set the default continuous-window cadence to 4-second windows beginning every 3 seconds.

## Impact

- Updates microphone command defaults and README guidance only.
- No new packages, models, processes, or external services.
