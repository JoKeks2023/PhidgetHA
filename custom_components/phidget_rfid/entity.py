"""Shared base entity for all Phidget RFID platforms."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo as HaDeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MANUFACTURER
from .coordinator import PhidgetRfidCoordinator

# Bitmask flags for entity.supported_features, used to gate which services
# Home Assistant lets a user call against a given entity (mirrors the
# light/climate convention of feature-flagging optional capabilities).
SUPPORT_WRITE_TAG = 1


class PhidgetRfidEntity(Entity):
    """Base class wiring up device info + coordinator push updates."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: PhidgetRfidCoordinator, unique_id_suffix: str) -> None:
        self.coordinator = coordinator
        info = coordinator.device_info
        serial = info.serial_number if info else "unknown"
        self._attr_unique_id = f"{serial}_{unique_id_suffix}"
        model = info.capabilities.display_name if info else "PhidgetRFID"
        model_id = info.capabilities.model_id if info else "unknown"
        sw_version = str(info.device_version) if info else None

        self._attr_device_info = HaDeviceInfo(
            identifiers={(DOMAIN, str(serial))},
            manufacturer=MANUFACTURER,
            name=f"{model} ({serial})",
            model=f"{model} ({model_id})",
            sw_version=sw_version,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, self.coordinator.signal, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self.coordinator.available
