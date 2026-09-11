"""Config flow for the Phidget RFID integration.

Prefers auto-discovery (enumerate attached Phidget RFID boards via
`PhidgetManager`) over asking the user to type a device path or serial number
by hand. Manual entry is offered as an explicit fallback ("Andere ...") for
cases where nothing is auto-detected (e.g. reader on a remote Phidget Network
Server, or discovery failing) rather than as a free-text default.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_CHANNEL,
    CONF_HUB_PORT,
    CONF_IS_HUB_PORT_DEVICE,
    CONF_MODEL,
    CONF_SERIAL_NUMBER,
    DEFAULT_CHANNEL,
    DOMAIN,
)
from .device import PhidgetRfidDevice, PhidgetRfidError

_LOGGER = logging.getLogger(__name__)

MANUAL_ENTRY = "__manual__"


def _scan_for_rfid_boards() -> list[tuple[int, str]]:
    """Best-effort enumeration of attached Phidget RFID boards.

    Runs in an executor. Returns (serial_number, device_name) pairs. Returns
    an empty list (never raises) if the native library is missing or
    discovery otherwise fails — manual entry remains available either way.
    """
    try:
        from Phidget22.Devices.RFID import RFID
        from Phidget22.PhidgetException import PhidgetException
    except ImportError:
        return []

    found: list[tuple[int, str]] = []
    try:
        probe = RFID()
        probe.openWaitForAttachment(1000)
        found.append((probe.getDeviceSerialNumber(), probe.getDeviceName()))
        probe.close()
    except PhidgetException:
        pass
    except Exception:
        _LOGGER.debug("Unexpected error during Phidget RFID discovery", exc_info=True)

    return found


class PhidgetRfidConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a single Phidget RFID reader."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: list[tuple[int, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            choice = user_input["device"]
            if choice == MANUAL_ENTRY:
                return await self.async_step_manual()
            serial_number = int(choice)
            return await self._async_try_connect(serial_number=serial_number, hub_port=None, channel=DEFAULT_CHANNEL, is_hub_port_device=False)

        self._discovered = await self.hass.async_add_executor_job(_scan_for_rfid_boards)

        options = {
            str(serial): f"{name} ({serial})" for serial, name in self._discovered
        }
        options[MANUAL_ENTRY] = "Andere / manuell eingeben"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("device"): vol.In(options)}),
            errors=errors,
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            return await self._async_try_connect(
                serial_number=user_input.get(CONF_SERIAL_NUMBER) or None,
                hub_port=user_input.get(CONF_HUB_PORT),
                channel=user_input.get(CONF_CHANNEL, DEFAULT_CHANNEL),
                is_hub_port_device=user_input.get(CONF_HUB_PORT) is not None,
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_SERIAL_NUMBER): int,
                vol.Optional(CONF_HUB_PORT): vol.All(int, vol.Range(min=0, max=5)),
                vol.Optional(CONF_CHANNEL, default=DEFAULT_CHANNEL): int,
            }
        )
        return self.async_show_form(step_id="manual", data_schema=schema, errors=errors)

    async def _async_try_connect(
        self,
        *,
        serial_number: int | None,
        hub_port: int | None,
        channel: int,
        is_hub_port_device: bool,
    ) -> ConfigFlowResult:
        device = PhidgetRfidDevice(
            self.hass,
            serial_number=serial_number,
            hub_port=hub_port,
            channel=channel,
            is_hub_port_device=is_hub_port_device,
        )
        try:
            info = await device.async_connect()
        except PhidgetRfidError as err:
            _LOGGER.warning("Config flow could not connect to reader: %s", err)
            return self.async_show_form(
                step_id="manual",
                data_schema=vol.Schema(
                    {
                        vol.Optional(CONF_SERIAL_NUMBER, default=serial_number): int,
                        vol.Optional(CONF_HUB_PORT, default=hub_port): vol.All(
                            int, vol.Range(min=0, max=5)
                        ),
                        vol.Optional(CONF_CHANNEL, default=channel): int,
                    }
                ),
                errors={"base": "cannot_connect"},
            )
        finally:
            await device.async_close()

        await self.async_set_unique_id(str(info.serial_number))
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"{info.capabilities.display_name} ({info.serial_number})",
            data={
                CONF_SERIAL_NUMBER: info.serial_number,
                CONF_HUB_PORT: hub_port,
                CONF_CHANNEL: channel,
                CONF_IS_HUB_PORT_DEVICE: is_hub_port_device,
                CONF_MODEL: info.capabilities.model_id,
            },
        )
