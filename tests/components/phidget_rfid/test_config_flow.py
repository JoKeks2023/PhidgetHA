"""Tests for the Phidget RFID config flow."""

from __future__ import annotations

from homeassistant.data_entry_flow import FlowResultType

from custom_components.phidget_rfid.config_flow import MANUAL_ENTRY
from custom_components.phidget_rfid.const import CONF_SERIAL_NUMBER, DOMAIN


async def test_discovered_device_creates_entry(hass, mock_phidget22):
    mock_phidget22.device_serial_number = 42

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device": "42"}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SERIAL_NUMBER] == 42


async def test_manual_entry_creates_entry(hass, mock_phidget22):
    mock_phidget22.device_serial_number = 99

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device": MANUAL_ENTRY}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"serial_number": 99, "channel": 0}
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SERIAL_NUMBER] == 99


async def test_duplicate_serial_aborts(hass, mock_phidget22):
    mock_phidget22.device_serial_number = 7

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device": "7"}
    )
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device": "7"}
    )
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_connect_failure_shows_error(hass, mock_phidget22):
    mock_phidget22.fail_on_open = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device": MANUAL_ENTRY}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"serial_number": 5, "channel": 0}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
