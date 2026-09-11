"""Thin async wrapper around one Phidget22 RFID channel.

All Phidget22 SDK calls are blocking (they hit the native libphidget22 C
library) and its event callbacks (`setOnTagHandler` etc.) fire on a Phidget22-
internal thread, not on the Home Assistant event loop. This module is the only
place that talks to `phidget22` directly; every other module goes through it.

NOTE on import path: the PyPI distribution is `phidget22` (lowercase, pinned
in manifest.json), but Phidgets' own language-binding source ships the
importable package as `Phidget22` (mixed case), matching their C#/Java-style
naming across all language bindings. This matches every official Phidget22
Python example seen during research; not independently confirmed against a
`pip install` on target hardware — see
docs/tasks/T-0001_phidget_rfid_integration/03_constraints.md.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.core import HomeAssistant

from .const import ATTACH_TIMEOUT_MS
from .models import ModelCapabilities, identify_model

_LOGGER = logging.getLogger(__name__)


class PhidgetRfidError(Exception):
    """Raised for any Phidget22 failure surfaced to Home Assistant."""


@dataclass
class RfidTagEvent:
    """One tag-detected event, already translated to our own vocabulary."""

    tag_id: str
    protocol: str


@dataclass
class DeviceInfo:
    serial_number: int
    device_name: str
    device_version: int
    hub_port: int | None
    channel: int
    capabilities: ModelCapabilities


class PhidgetRfidDevice:
    """Owns exactly one Phidget22 RFID channel for one physical reader."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        serial_number: int | None,
        hub_port: int | None,
        channel: int,
        is_hub_port_device: bool,
    ) -> None:
        self._hass = hass
        self._serial_number = serial_number
        self._hub_port = hub_port
        self._channel = channel
        self._is_hub_port_device = is_hub_port_device

        self._rfid = None  # Phidget22 RFID channel instance, created lazily.
        self._device_info: DeviceInfo | None = None

        self._on_tag: Callable[[RfidTagEvent], None] | None = None
        self._on_tag_lost: Callable[[str], None] | None = None
        self._on_attach: Callable[[], None] | None = None
        self._on_detach: Callable[[], None] | None = None
        self._on_error: Callable[[str], None] | None = None

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._device_info

    @property
    def is_attached(self) -> bool:
        if self._rfid is None:
            return False
        try:
            return bool(self._rfid.getAttached())
        except Exception:  # noqa: BLE001 - defensive, see module docstring
            return False

    def set_listeners(
        self,
        *,
        on_tag: Callable[[RfidTagEvent], None] | None = None,
        on_tag_lost: Callable[[str], None] | None = None,
        on_attach: Callable[[], None] | None = None,
        on_detach: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """Register callbacks. All are invoked on the HA event loop thread."""
        if on_tag is not None:
            self._on_tag = on_tag
        if on_tag_lost is not None:
            self._on_tag_lost = on_tag_lost
        if on_attach is not None:
            self._on_attach = on_attach
        if on_detach is not None:
            self._on_detach = on_detach
        if on_error is not None:
            self._on_error = on_error

    async def async_connect(self) -> DeviceInfo:
        """Open the channel and wait for attachment. Runs blocking SDK calls in executor."""
        return await self._hass.async_add_executor_job(self._connect_blocking)

    async def async_close(self) -> None:
        await self._hass.async_add_executor_job(self._close_blocking)

    async def async_write_tag(self, tag_data: str, protocol: str, lock_tag: bool) -> None:
        if self._device_info is None or not self._device_info.capabilities.can_write:
            raise PhidgetRfidError("This reader model does not support writing tags")
        await self._hass.async_add_executor_job(
            self._write_blocking, tag_data, protocol, lock_tag
        )

    async def async_set_antenna_enabled(self, enabled: bool) -> None:
        if self._device_info is None or not self._device_info.capabilities.has_antenna_control:
            raise PhidgetRfidError("This reader model does not support antenna control")
        await self._hass.async_add_executor_job(self._set_antenna_blocking, enabled)

    # -- blocking helpers, executed via async_add_executor_job only ---------

    def _connect_blocking(self) -> DeviceInfo:
        try:
            from Phidget22.Devices.RFID import RFID
            from Phidget22.PhidgetException import PhidgetException
        except ImportError as err:  # pragma: no cover - exercised via mocks in tests
            raise PhidgetRfidError(
                "phidget22 package (Phidget22 native library) is not installed"
            ) from err

        rfid = RFID()

        if self._serial_number is not None:
            rfid.setDeviceSerialNumber(self._serial_number)
        if self._is_hub_port_device and self._hub_port is not None:
            rfid.setHubPort(self._hub_port)
            rfid.setIsHubPortDevice(True)
        rfid.setChannel(self._channel)

        rfid.setOnTagHandler(self._make_thread_safe(self._handle_tag))
        rfid.setOnTagLostHandler(self._make_thread_safe(self._handle_tag_lost))
        rfid.setOnAttachHandler(self._make_thread_safe(self._handle_attach))
        rfid.setOnDetachHandler(self._make_thread_safe(self._handle_detach))
        rfid.setOnErrorHandler(self._make_thread_safe(self._handle_error))

        try:
            rfid.openWaitForAttachment(ATTACH_TIMEOUT_MS)
        except PhidgetException as err:
            raise PhidgetRfidError(f"Failed to open Phidget RFID channel: {err}") from err

        self._rfid = rfid

        device_name = rfid.getDeviceName()
        device_version = rfid.getDeviceVersion()
        serial_number = rfid.getDeviceSerialNumber()
        capabilities = identify_model(device_name=device_name, device_version=device_version)

        info = DeviceInfo(
            serial_number=serial_number,
            device_name=device_name,
            device_version=device_version,
            hub_port=self._hub_port if self._is_hub_port_device else None,
            channel=self._channel,
            capabilities=capabilities,
        )
        self._device_info = info
        return info

    def _close_blocking(self) -> None:
        if self._rfid is None:
            return
        try:
            self._rfid.close()
        except Exception:
            _LOGGER.debug("Error closing Phidget RFID channel", exc_info=True)
        finally:
            self._rfid = None

    def _write_blocking(self, tag_data: str, protocol: str, lock_tag: bool) -> None:
        from Phidget22.PhidgetException import PhidgetException
        from Phidget22.RFIDProtocol import RFIDProtocol

        try:
            protocol_value = getattr(RFIDProtocol, protocol)
        except AttributeError as err:
            raise PhidgetRfidError(f"Unknown RFID protocol '{protocol}'") from err

        assert self._rfid is not None
        try:
            self._rfid.write(tag_data, protocol_value, lock_tag)
        except PhidgetException as err:
            raise PhidgetRfidError(f"Failed to write tag: {err}") from err

    def _set_antenna_blocking(self, enabled: bool) -> None:
        from Phidget22.PhidgetException import PhidgetException

        assert self._rfid is not None
        try:
            self._rfid.setAntennaEnabled(enabled)
        except PhidgetException as err:
            raise PhidgetRfidError(f"Failed to set antenna state: {err}") from err

    # -- Phidget22 callbacks (native thread) ---------------------------------

    def _make_thread_safe(self, fn: Callable[..., None]) -> Callable[..., None]:
        """Wrap a callback so it always runs on the HA event loop, not the SDK thread."""

        def _wrapper(*args: object) -> None:
            self._hass.loop.call_soon_threadsafe(fn, *args)

        return _wrapper

    def _handle_tag(self, _channel: object, tag: str, protocol: object) -> None:
        if self._on_tag is None:
            return
        protocol_name = getattr(protocol, "name", str(protocol))
        self._on_tag(RfidTagEvent(tag_id=tag, protocol=protocol_name))

    def _handle_tag_lost(self, _channel: object, tag: str) -> None:
        if self._on_tag_lost is not None:
            self._on_tag_lost(tag)

    def _handle_attach(self, _channel: object) -> None:
        if self._on_attach is not None:
            self._on_attach()

    def _handle_detach(self, _channel: object) -> None:
        if self._on_detach is not None:
            self._on_detach()

    def _handle_error(self, _channel: object, _code: object, description: str) -> None:
        _LOGGER.warning("Phidget RFID error: %s", description)
        if self._on_error is not None:
            self._on_error(description)
