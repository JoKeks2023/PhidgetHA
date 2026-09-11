"""Binary sensor platform for the Phidget RFID integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PhidgetRfidCoordinator
from .entity import PhidgetRfidEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PhidgetRfidCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PhidgetRfidTagPresentSensor(coordinator),
            PhidgetRfidConnectivitySensor(coordinator),
        ]
    )


class PhidgetRfidTagPresentSensor(PhidgetRfidEntity, BinarySensorEntity):
    """Whether a tag is currently in range of the antenna."""

    _attr_translation_key = "tag_present"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator: PhidgetRfidCoordinator) -> None:
        super().__init__(coordinator, "tag_present")

    @property
    def is_on(self) -> bool:
        return self.coordinator.tag_present


class PhidgetRfidConnectivitySensor(PhidgetRfidEntity, BinarySensorEntity):
    """Whether the reader is currently connected and attached over USB."""

    _attr_translation_key = "connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: PhidgetRfidCoordinator) -> None:
        super().__init__(coordinator, "connectivity")

    @property
    def is_on(self) -> bool:
        return self.coordinator.available

    @property
    def available(self) -> bool:
        # Unlike other entities, connectivity itself must stay available
        # even while the reader is disconnected, or the diagnostic is useless.
        return True
