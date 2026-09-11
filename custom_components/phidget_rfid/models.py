"""Capability abstraction for the Phidgets RFID product family.

Home Assistant code (config flow, entities, services) must never branch on a
specific model string such as ``"1024_0B"``. It asks a :class:`ModelCapabilities`
instance instead. See docs/tasks/T-0001_phidget_rfid_integration/03_constraints.md
for the doc-verified source of these capability values.

Protocol/chipset identifiers are plain strings here (not the phidget22
library's own enum) so this module has no import-time dependency on the
`phidget22` package and can be unit-tested/imported during config flow
schema building without the native library present. `device.py` maps these
strings to the real `phidget22.RFIDProtocol` enum members by name.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PROTOCOL_EM4100 = "EM4100"
PROTOCOL_ISO11785_FDX_B = "ISO11785_FDX_B"
PROTOCOL_PHIDGET_TAG = "PHIDGET_TAG"
# Read support claimed on the 1024_1 product page; the corresponding
# phidget22.RFIDProtocol enum member names are NOT verified against the
# current SDK (see constraints doc). Resolved defensively in device.py.
PROTOCOL_HID_GENERIC = "HID_GENERIC"
PROTOCOL_HID_26BIT = "HID_26BIT"

CHIPSET_T5577 = "T5577"
CHIPSET_EM4305 = "EM4305"

STATUS_CURRENT = "current"
STATUS_NRND = "nrnd"
STATUS_DISCONTINUED = "discontinued"


@dataclass(frozen=True, kw_only=True)
class ModelCapabilities:
    """Doc-verified capabilities of one Phidgets RFID board model."""

    model_id: str
    display_name: str
    read_protocols: tuple[str, ...]
    can_write: bool
    write_chipsets: tuple[str, ...] = field(default_factory=tuple)
    # Onboard LED exists on every RFID board per product pages, but no
    # `setLEDOn`-style method was found on the Phidget22 RFID channel class
    # itself (see constraints doc) — likely a separate DigitalOutput channel.
    # Kept False (unverified) until confirmed against real hardware/SDK.
    has_led_verified: bool = False
    has_antenna_control: bool = True
    status: str = STATUS_CURRENT

    @property
    def can_read(self) -> bool:
        return bool(self.read_protocols)


MODEL_1023_0 = ModelCapabilities(
    model_id="1023_0",
    display_name="PhidgetRFID",
    read_protocols=(PROTOCOL_EM4100,),
    can_write=False,
    status=STATUS_DISCONTINUED,
)

MODEL_1023_1 = ModelCapabilities(
    model_id="1023_1",
    display_name="PhidgetRFID",
    read_protocols=(PROTOCOL_EM4100,),
    can_write=False,
    status=STATUS_DISCONTINUED,
)

MODEL_1024_0 = ModelCapabilities(
    model_id="1024_0",
    display_name="PhidgetRFID Read-Write",
    read_protocols=(PROTOCOL_EM4100, PROTOCOL_ISO11785_FDX_B, PROTOCOL_PHIDGET_TAG),
    can_write=True,
    write_chipsets=(CHIPSET_T5577,),
    status=STATUS_NRND,
)

MODEL_1024_0B = ModelCapabilities(
    model_id="1024_0B",
    display_name="PhidgetRFID Read-Write",
    read_protocols=(PROTOCOL_EM4100, PROTOCOL_ISO11785_FDX_B, PROTOCOL_PHIDGET_TAG),
    can_write=True,
    write_chipsets=(CHIPSET_T5577,),
    status=STATUS_NRND,
)

MODEL_1024_1 = ModelCapabilities(
    model_id="1024_1",
    display_name="PhidgetRFID Read-Write",
    read_protocols=(
        PROTOCOL_EM4100,
        PROTOCOL_ISO11785_FDX_B,
        PROTOCOL_PHIDGET_TAG,
        PROTOCOL_HID_GENERIC,
        PROTOCOL_HID_26BIT,
    ),
    can_write=True,
    write_chipsets=(CHIPSET_T5577, CHIPSET_EM4305),
    status=STATUS_CURRENT,
)

# Conservative fallback for a device we cannot positively identify: assume
# only the capability every known board has (EM4100 read), nothing else.
# Never assume write support for an unrecognized model.
MODEL_UNKNOWN = ModelCapabilities(
    model_id="unknown",
    display_name="Unknown Phidgets RFID device",
    read_protocols=(PROTOCOL_EM4100,),
    can_write=False,
    has_antenna_control=False,
    status=STATUS_DISCONTINUED,
)

_ALL_MODELS: tuple[ModelCapabilities, ...] = (
    MODEL_1023_0,
    MODEL_1023_1,
    MODEL_1024_0,
    MODEL_1024_0B,
    MODEL_1024_1,
)

MODELS_BY_ID = {model.model_id: model for model in _ALL_MODELS}


def identify_model(*, device_name: str, device_version: int | None) -> ModelCapabilities:
    """Map a Phidget22 `getDeviceName()` string (+ optional version) to capabilities.

    Phidget22's RFID channel does not expose the marketing model number
    (e.g. "1024_0B") directly — only a human-readable device name and an
    integer device/firmware version. Distinguishing 1024_0/1024_0B/1024_1 by
    `getDeviceVersion()` alone is NOT verified against official docs; where
    the version can't be mapped with confidence, this falls back to the
    common-denominator 1024_0B capability set (safe: every 1024-series board
    supports at least EM4100/ISO11785 FDX-B/PhidgetTAG read + T5577 write).
    """
    name = (device_name or "").strip().lower()

    if "read-write" in name or "read/write" in name:
        # Known device_version boundary is not documented; only trust an
        # explicit, high version number as a signal for the newest board.
        if device_version is not None and device_version >= 300:
            return MODEL_1024_1
        return MODEL_1024_0B

    if "rfid" in name:
        return MODEL_1023_1

    return MODEL_UNKNOWN
