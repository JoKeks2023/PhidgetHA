"""Sensor platform for the Phidget RFID integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_LOCK_TAG, ATTR_PROTOCOL, ATTR_TAG_DATA, DOMAIN, SERVICE_WRITE_TAG
from .coordinator import PhidgetRfidCoordinator
from .device import PhidgetRfidError
from .entity import SUPPORT_WRITE_TAG, PhidgetRfidEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PhidgetRfidCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PhidgetRfidLastTagSensor(coordinator)])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_WRITE_TAG,
        {
            vol.Required(ATTR_TAG_DATA): cv.string,
            vol.Required(ATTR_PROTOCOL): cv.string,
            vol.Optional(ATTR_LOCK_TAG, default=False): cv.boolean,
        },
        "async_handle_write_tag",
        required_features=[SUPPORT_WRITE_TAG],
    )


class PhidgetRfidLastTagSensor(PhidgetRfidEntity):
    """Last RFID tag ID read by this reader."""

    _attr_translation_key = "last_tag"
    _attr_icon = "mdi:card-account-details"

    def __init__(self, coordinator: PhidgetRfidCoordinator) -> None:
        super().__init__(coordinator, "last_tag")
        info = coordinator.device_info
        if info and info.capabilities.can_write:
            self._attr_supported_features = SUPPORT_WRITE_TAG

    @property
    def native_value(self) -> str | None:
        return self.coordinator.last_tag_id

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {ATTR_PROTOCOL: self.coordinator.last_tag_protocol}

    async def async_handle_write_tag(self, call: ServiceCall) -> None:
        try:
            await self.coordinator.device.async_write_tag(
                call.data[ATTR_TAG_DATA],
                call.data[ATTR_PROTOCOL],
                call.data[ATTR_LOCK_TAG],
            )
        except PhidgetRfidError as err:
            raise ServiceValidationError(str(err)) from err
