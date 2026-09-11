"""Diagnostics support for the Phidget RFID integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PhidgetRfidCoordinator

REDACT_KEYS = {"serial_number"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: PhidgetRfidCoordinator = hass.data[DOMAIN][entry.entry_id]
    info = coordinator.device_info

    return {
        "available": coordinator.available,
        "tag_present": coordinator.tag_present,
        "last_tag_protocol": coordinator.last_tag_protocol,
        "device": {
            "device_name": info.device_name if info else None,
            "device_version": info.device_version if info else None,
            "model_id": info.capabilities.model_id if info else None,
            "read_protocols": list(info.capabilities.read_protocols) if info else [],
            "can_write": info.capabilities.can_write if info else None,
            "write_chipsets": list(info.capabilities.write_chipsets) if info else [],
            "status": info.capabilities.status if info else None,
        }
        if info
        else None,
    }
