"""Connection lifecycle and push-state distribution for one RFID reader.

This is deliberately not a `DataUpdateCoordinator` — there is nothing to poll.
State changes are pushed by Phidget22 event callbacks (via `device.py`) and
distributed to entities through Home Assistant's dispatcher signal helper.
"""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later

from .const import (
    ATTR_PROTOCOL,
    ATTR_READER,
    ATTR_TAG_ID,
    EVENT_TAG_DETECTED,
    EVENT_TAG_LOST,
    RECONNECT_MAX_DELAY,
    RECONNECT_MIN_DELAY,
    SIGNAL_UPDATE,
)
from .device import DeviceInfo, PhidgetRfidDevice, PhidgetRfidError, RfidTagEvent

_LOGGER = logging.getLogger(__name__)


class PhidgetRfidCoordinator:
    """Owns a `PhidgetRfidDevice`, keeps it connected, publishes state."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        device: PhidgetRfidDevice,
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.device = device

        self.available = False
        self.last_tag_id: str | None = None
        self.last_tag_protocol: str | None = None
        self.tag_present = False
        self.device_info: DeviceInfo | None = None

        self._signal = SIGNAL_UPDATE.format(entry_id=entry_id)
        self._reconnect_delay = RECONNECT_MIN_DELAY
        self._reconnect_unsub = None
        self._shutting_down = False

        device.set_listeners(
            on_tag=self._handle_tag,
            on_tag_lost=self._handle_tag_lost,
            on_attach=self._handle_attach,
            on_detach=self._handle_detach,
            on_error=self._handle_error,
        )

    @property
    def signal(self) -> str:
        return self._signal

    async def async_setup(self) -> None:
        await self._async_connect()

    async def async_unload(self) -> None:
        self._shutting_down = True
        if self._reconnect_unsub is not None:
            self._reconnect_unsub()
            self._reconnect_unsub = None
        await self.device.async_close()

    async def _async_connect(self) -> None:
        try:
            self.device_info = await self.device.async_connect()
        except PhidgetRfidError as err:
            _LOGGER.warning("Could not connect to Phidget RFID reader: %s", err)
            self.available = False
            self._schedule_reconnect()
            return

        self.available = True
        self._reconnect_delay = RECONNECT_MIN_DELAY
        self._publish()

    def _schedule_reconnect(self) -> None:
        if self._shutting_down or self._reconnect_unsub is not None:
            return

        def _retry(_now: object) -> None:
            self._reconnect_unsub = None
            self.hass.async_create_task(self._async_connect())

        self._reconnect_unsub = async_call_later(self.hass, self._reconnect_delay, _retry)
        self._reconnect_delay = min(self._reconnect_delay * 2, RECONNECT_MAX_DELAY)

    def _handle_tag(self, event: RfidTagEvent) -> None:
        self.last_tag_id = event.tag_id
        self.last_tag_protocol = event.protocol
        self.tag_present = True
        self._publish()

        reader_name = self.device_info.capabilities.display_name if self.device_info else "PhidgetRFID"
        self.hass.bus.async_fire(
            EVENT_TAG_DETECTED,
            {
                ATTR_TAG_ID: event.tag_id,
                ATTR_PROTOCOL: event.protocol,
                ATTR_READER: reader_name,
            },
        )

    def _handle_tag_lost(self, tag: str) -> None:
        self.tag_present = False
        self._publish()
        self.hass.bus.async_fire(EVENT_TAG_LOST, {ATTR_TAG_ID: tag})

    def _handle_attach(self) -> None:
        _LOGGER.info("Phidget RFID reader attached")
        self.available = True
        self._reconnect_delay = RECONNECT_MIN_DELAY
        self._publish()

    def _handle_detach(self) -> None:
        _LOGGER.warning("Phidget RFID reader detached, will attempt to reconnect")
        self.available = False
        self.tag_present = False
        self._publish()
        self._schedule_reconnect()

    def _handle_error(self, description: str) -> None:
        _LOGGER.debug("Phidget RFID reported error: %s", description)

    def _publish(self) -> None:
        async_dispatcher_send(self.hass, self._signal)
