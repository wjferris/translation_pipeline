## Why

The next live comparison should favor recognition quality and more context per translation-ready segment. The local Medium Whisper model is installed, and a 5-second window every 4 seconds retains the successful one-second overlap while giving Whisper more speech context than the current 4/3 Small baseline.

## What Changes

- Select the installed local Medium Whisper model in `.env`.
- Set live microphone defaults to 5-second windows every 4 seconds.
- Update the documented baseline.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `live-microphone-transcription`: Set the default continuous-window cadence to 5-second windows beginning every 4 seconds.

## Impact

- Updates local model configuration, command defaults, and documentation only.
