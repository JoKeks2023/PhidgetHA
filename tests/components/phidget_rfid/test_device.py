"""Tests for the PhidgetRfidDevice async wrapper."""

from __future__ import annotations

import pytest

from custom_components.phidget_rfid.device import (
    PhidgetRfidDevice,
    PhidgetRfidError,
    RfidTagEvent,
)
from custom_components.phidget_rfid.models import MODEL_1024_0B, MODEL_1024_1


async def test_connect_identifies_1024_0b_by_default(hass, mock_phidget22):
    mock_phidget22.device_name = "PhidgetRFID Read-Write"
    mock_phidget22.device_version = 100
    mock_phidget22.device_serial_number = 555111

    device = PhidgetRfidDevice(
        hass, serial_number=555111, hub_port=None, channel=0, is_hub_port_device=False
    )
    info = await device.async_connect()

    assert info.serial_number == 555111
    assert info.capabilities is MODEL_1024_0B
    assert device.is_attached

    fake = mock_phidget22.instances[-1]
    assert ("setDeviceSerialNumber", (555111,)) in fake.calls
    assert ("setChannel", (0,)) in fake.calls

    await device.async_close()
    assert not device.is_attached


async def test_connect_identifies_1024_1_by_high_version(hass, mock_phidget22):
    mock_phidget22.device_version = 320
    device = PhidgetRfidDevice(
        hass, serial_number=None, hub_port=None, channel=0, is_hub_port_device=False
    )
    info = await device.async_connect()
    assert info.capabilities is MODEL_1024_1
    await device.async_close()


async def test_connect_failure_raises_phidget_rfid_error(hass, mock_phidget22):
    mock_phidget22.fail_on_open = True
    device = PhidgetRfidDevice(
        hass, serial_number=None, hub_port=None, channel=0, is_hub_port_device=False
    )
    with pytest.raises(PhidgetRfidError):
        await device.async_connect()


async def test_tag_event_reaches_registered_listener(hass, mock_phidget22):
    device = PhidgetRfidDevice(
        hass, serial_number=None, hub_port=None, channel=0, is_hub_port_device=False
    )
    seen: list[RfidTagEvent] = []
    device.set_listeners(on_tag=seen.append)
    await device.async_connect()

    fake = mock_phidget22.instances[-1]
    fake.simulate_tag("04A1B2C3D4")
    await hass.async_block_till_done()

    assert len(seen) == 1
    assert seen[0].tag_id == "04A1B2C3D4"
    assert seen[0].protocol == "EM4100"


async def test_detach_reaches_registered_listener(hass, mock_phidget22):
    device = PhidgetRfidDevice(
        hass, serial_number=None, hub_port=None, channel=0, is_hub_port_device=False
    )
    detached = []
    device.set_listeners(on_detach=lambda: detached.append(True))
    await device.async_connect()

    fake = mock_phidget22.instances[-1]
    fake.simulate_detach()
    await hass.async_block_till_done()

    assert detached == [True]


async def test_write_tag_rejected_for_read_only_model(hass, mock_phidget22):
    mock_phidget22.device_name = "PhidgetRFID"  # 1023_1, read-only
    device = PhidgetRfidDevice(
        hass, serial_number=None, hub_port=None, channel=0, is_hub_port_device=False
    )
    await device.async_connect()

    with pytest.raises(PhidgetRfidError):
        await device.async_write_tag("data", "EM4100", False)


async def test_write_tag_succeeds_for_read_write_model(hass, mock_phidget22):
    device = PhidgetRfidDevice(
        hass, serial_number=None, hub_port=None, channel=0, is_hub_port_device=False
    )
    await device.async_connect()

    await device.async_write_tag("04A1B2C3D4", "EM4100", True)

    fake = mock_phidget22.instances[-1]
    write_calls = [c for c in fake.calls if c[0] == "write"]
    assert len(write_calls) == 1
    _, (tag_data, protocol, lock_tag) = write_calls[0]
    assert tag_data == "04A1B2C3D4"
    assert protocol.name == "EM4100"
    assert lock_tag is True
