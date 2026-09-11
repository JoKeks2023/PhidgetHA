# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - Unreleased

### Added

- Initial `phidget_rfid` custom integration (config flow, coordinator, device
  registry, sensor, binary sensors, diagnostics).
- Capability abstraction layer (`models.py`) covering Phidgets RFID models
  1023_0, 1023_1, 1024_0, 1024_0B, 1024_1.
- `phidget_rfid_tag` / `phidget_rfid_tag_lost` Home Assistant events.
- `phidget_rfid.write_tag` service, gated on device write capability.
- Reconnect logic with exponential backoff for USB disconnect/reconnect.
- Unit test suite with a fully mocked `Phidget22` package (no hardware
  required to run tests).
- Diagnostics export, DE/EN translations.

### Known limitations (see README)

- LED control not implemented — could not verify a Phidget22 RFID-channel
  LED method against official docs; documented as a future extension.
- Antenna on/off control implemented in `device.py` but not yet exposed as a
  Home Assistant service/entity (not part of the original scope).
- HID 26-bit / HID Generic protocol support (1024_1 only) is declared in the
  capability model but not exercised against real hardware/SDK.
