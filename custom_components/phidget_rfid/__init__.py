"""The Phidget RFID integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CHANNEL,
    CONF_HUB_PORT,
    CONF_IS_HUB_PORT_DEVICE,
    CONF_SERIAL_NUMBER,
    DOMAIN,
)
from .coordinator import PhidgetRfidCoordinator
from .device import PhidgetRfidDevice

PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    device = PhidgetRfidDevice(
        hass,
        serial_number=entry.data.get(CONF_SERIAL_NUMBER),
        hub_port=entry.data.get(CONF_HUB_PORT),
        channel=entry.data.get(CONF_CHANNEL, 0),
        is_hub_port_device=entry.data.get(CONF_IS_HUB_PORT_DEVICE, False),
    )
    coordinator = PhidgetRfidCoordinator(hass, entry.entry_id, device)
    await coordinator.async_setup()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator: PhidgetRfidCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_unload()
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
