# PhidgetHA

A native Home Assistant **custom integration** for Phidgets RFID readers —
built around the [Phidget22](https://www.phidgets.com/docs22/) SDK, talking
directly to the USB reader from inside Home Assistant Core. No add-on, no
MQTT broker, no external server required.

Reference hardware: **PhidgetRFID Read-Write 1024_0B**, attached directly via
USB to a Raspberry Pi running Home Assistant OS. The integration is generic
across the whole Phidgets RFID product family — see [Supported
hardware](#supported-hardware).

```text
PhidgetRFID reader
      │ USB
      ▼
Raspberry Pi / Home Assistant OS
      │
      ▼
custom_components/phidget_rfid  (this repo)
      │  Phidget22 (phidget22 PyPI package)
      ▼
Home Assistant Core
  ├── phidget_rfid_tag / phidget_rfid_tag_lost events
  ├── Device + Entities (sensor, binary_sensor)
  └── phidget_rfid.write_tag service (read-write readers only)
```

## Why no add-on?

An earlier design considered a separate Home Assistant OS add-on to isolate
the native `libphidget22` library from Home Assistant Core. After checking
the current Home Assistant Supervisor source and developer docs, that turned
out to be unnecessary and, for this integration, not the better trade-off:

- The Home Assistant Core container under Home Assistant OS already gets raw
  USB device-cgroup access (`PolicyGroup.USB`, `/dev/bus/usb/*`) — an add-on
  is not required just to reach the USB device.
- Home Assistant Core's own "Dependency Transparency" rule requires a
  dependency to come from a public source repository with public CI. The
  `phidget22` PyPI package is vendor-distributed only (no public repo) — so
  this integration **can never be accepted into Home Assistant Core**,
  regardless of whether it uses an add-on or not. The one architectural
  advantage an add-on would still offer (crash isolation: a fault in the
  native library can't take down all of Home Assistant Core) is a real,
  accepted trade-off of this design, mitigated with defensive error handling
  and automatic reconnect rather than eliminated.

See `docs/tasks/T-0001_phidget_rfid_integration/` for the full research
trail and constraints this decision is based on.

## Supported hardware

Capabilities are detected per-device, not hardcoded — a reader is asked what
it supports (`custom_components/phidget_rfid/models.py`) rather than the
integration assuming one model. Entities/services that a given reader
doesn't support (e.g. writing tags) are simply not offered for it.

| Model | Read protocols | Write | Status |
|---|---|---|---|
| 1023_0 | EM4100 | — | discontinued |
| 1023_1 | EM4100 | — | discontinued |
| 1024_0 | EM4100, ISO11785 FDX-B, PhidgetTAG | T5577 | NRND |
| **1024_0B** (reference device) | EM4100, ISO11785 FDX-B, PhidgetTAG | T5577 | NRND |
| 1024_1 | EM4100, ISO11785 FDX-B, PhidgetTAG, HID 26-bit*, HID Generic* | T5577, EM4305 | current |

`*` Read support claimed on the Phidgets product page; the corresponding
`phidget22.RFIDProtocol` enum member names are not verified against the
current SDK — see constraints doc. Model detection itself
(`identify_model()`) uses the reader's `getDeviceName()` string and
`getDeviceVersion()` as a heuristic (Phidget22 does not expose a marketing
model number like "1024_0B" directly) and falls back to a safe, read-only,
no-write capability set for anything it can't positively identify — it never
assumes write support.

## Installation

Not yet published to HACS. Manual install:

1. Copy `custom_components/phidget_rfid` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → Phidget RFID.**
4. Plug in the reader before starting the config flow — auto-detected
   devices are listed by serial number; choose "Other / manual entry" if
   yours isn't found (e.g. a reader on a Phidget Network Server).

## Events

```yaml
triggers:
  - trigger: event
    event_type: phidget_rfid_tag

actions:
  - action: persistent_notification.create
    data:
      title: "RFID"
      message: "Tag erkannt: {{ trigger.event.data.tag_id }}"
```

`phidget_rfid_tag` data: `tag_id`, `protocol`, `reader`.
`phidget_rfid_tag_lost` data: `tag_id`.

## Entities

- `sensor.<reader>_last_tag` — last tag ID read; `protocol` attribute.
- `binary_sensor.<reader>_tag_detected` — a tag is currently in range.
- `binary_sensor.<reader>_connectivity` (diagnostic) — reader attached/USB
  connected.

Firmware/hardware version and model are shown on the device page (Device
Registry), not as separate entities, to avoid entity clutter.

## Services

`phidget_rfid.write_tag` — only offered for entities whose reader supports
writing (T5577/EM4305-based readers: 1024_0, 1024_0B, 1024_1).

```yaml
action: phidget_rfid.write_tag
target:
  entity_id: sensor.phidgetrfid_read_write_555111_last_tag
data:
  tag_data: "0123456789"
  protocol: "EM4100"
  lock_tag: false
```

## Not implemented (documented, not invented)

- **LED control** — no `setLEDOn`-style method was found on the Phidget22
  `RFID` channel class in any primary source checked during research; the
  onboard LED is likely a separate `DigitalOutput` channel on the same
  board. Left out rather than guessed at. Future extension once confirmed
  against the real SDK/hardware.
- **Antenna on/off** (`setAntennaEnabled`) — implemented in `device.py`
  (verified API) but not yet exposed as a Home Assistant service, since it
  wasn't part of the original request. Straightforward to add.
- **VINT hub operation** — architecture supports it (`hub_port`/
  `is_hub_port_device` config), but only direct USB has been exercised.

## Reconnect behaviour

USB disconnect fires Phidget22's `onDetach` handler, which marks the
connectivity binary sensor "off" and schedules a reconnect attempt with
exponential backoff (5s up to 300s) — no manual restart of the integration
should be required. This is implemented and unit-tested with a mocked
`Phidget22` package; **actual USB unplug/replug behavior on real Home
Assistant OS + real hardware has not been verified** (flagged honestly, not
hidden) — see the hardware test checklist below.

## Multiple readers

Each config entry addresses one reader by serial number (or hub
port + channel for VINT-connected devices), so multiple readers can be added
as separate Home Assistant devices. Only tested with one physical reader.

## Development & testing

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
pytest
```

The entire `Phidget22` package is mocked in
`tests/components/phidget_rfid/conftest.py` — no real hardware or native
library is needed to run the suite. As of this writing: **22 tests, all
passing**, run against `homeassistant==2026.9.1` /
`pytest-homeassistant-custom-component==0.13.364`.

## Hardware test checklist (real Raspberry Pi + real reader)

1. Find your reader's Phidget serial number: with the Phidget Control Panel
   (Windows/macOS) or, on Linux, run a short Python snippet using
   `phidget22`'s `PhidgetManager` — or just let the config flow's
   auto-discovery show it to you.
2. Install this integration (see Installation), plug in the reader.
3. **Settings → Devices & Services → Add Integration → Phidget RFID** — the
   reader should appear as a discovered option; select it.
4. Check **Settings → System → Logs** (filter `phidget_rfid`) for
   connect/attach confirmation.
5. Hold a tag against the reader — `binary_sensor.*_tag_detected` should
   turn on, `sensor.*_last_tag` should update.
6. In **Developer Tools → Events**, listen to `phidget_rfid_tag` and confirm
   the event fires with `tag_id`/`protocol`/`reader`.
7. Build the example automation above and confirm the notification appears.
8. Unplug the USB reader: `binary_sensor.*_connectivity` should turn off
   within a few seconds, without any error requiring an integration reload.
9. Plug it back in: connectivity should return to "on" automatically
   (reconnect backoff, up to a few minutes worst case) — **this step is the
   one most worth double-checking on real hardware**, since USB hotplug
   detection quality inside the Home Assistant Core container is not fully
   documented upstream.
10. To diagnose USB issues: `lsusb` should show a Phidgets device
    (vendor ID `06c2`); check Home Assistant logs for `PhidgetRfidError`
    messages, which include the underlying Phidget22 error text.
11. To restart just this integration: **Settings → Devices & Services →
    Phidget RFID → ⋮ → Reload** (no full Home Assistant restart needed).

## Architecture / task documentation

Full research trail, constraints, and scope for this integration are kept in
`docs/tasks/T-0001_phidget_rfid_integration/`.

## License

MIT, see `LICENSE`.
