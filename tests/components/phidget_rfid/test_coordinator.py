"""Tests for PhidgetRfidCoordinator: event firing, push updates, reconnect."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.phidget_rfid.const import EVENT_TAG_DETECTED, EVENT_TAG_LOST
from custom_components.phidget_rfid.coordinator import PhidgetRfidCoordinator
from custom_components.phidget_rfid.device import PhidgetRfidDevice


async def _setup_coordinator(hass, mock_phidget22):
    device = PhidgetRfidDevice(
        hass, serial_number=None, hub_port=None, channel=0, is_hub_port_device=False
    )
    coordinator = PhidgetRfidCoordinator(hass, "test-entry", device)
    await coordinator.async_setup()
    await hass.async_block_till_done()
    return coordinator


async def test_tag_detected_fires_event_and_updates_state(hass, mock_phidget22):
    coordinator = await _setup_coordinator(hass, mock_phidget22)
    events = async_capture_events(hass, EVENT_TAG_DETECTED)

    fake = mock_phidget22.instances[-1]
    fake.simulate_tag("04A1B2C3D4")
    await hass.async_block_till_done()

    assert coordinator.last_tag_id == "04A1B2C3D4"
    assert coordinator.tag_present is True
    assert len(events) == 1
    assert events[0].data["tag_id"] == "04A1B2C3D4"
    assert events[0].data["protocol"] == "EM4100"
    assert events[0].data["reader"]

    await coordinator.async_unload()


async def test_tag_lost_fires_event_and_clears_presence(hass, mock_phidget22):
    coordinator = await _setup_coordinator(hass, mock_phidget22)
    fake = mock_phidget22.instances[-1]
    fake.simulate_tag("04A1B2C3D4")
    await hass.async_block_till_done()

    events = async_capture_events(hass, EVENT_TAG_LOST)
    fake.simulate_tag_lost("04A1B2C3D4")
    await hass.async_block_till_done()

    assert coordinator.tag_present is False
    assert len(events) == 1

    await coordinator.async_unload()


async def test_detach_marks_unavailable_and_schedules_reconnect(hass, mock_phidget22):
    coordinator = await _setup_coordinator(hass, mock_phidget22)
    assert coordinator.available is True

    fake = mock_phidget22.instances[-1]
    fake.simulate_detach()
    await hass.async_block_till_done()

    assert coordinator.available is False
    assert coordinator.tag_present is False
    # A reconnect timer must be scheduled, not left to a manual restart.
    assert coordinator._reconnect_unsub is not None

    await coordinator.async_unload()


async def test_connect_failure_schedules_reconnect_without_raising(hass, mock_phidget22):
    mock_phidget22.fail_on_open = True
    device = PhidgetRfidDevice(
        hass, serial_number=None, hub_port=None, channel=0, is_hub_port_device=False
    )
    coordinator = PhidgetRfidCoordinator(hass, "test-entry-2", device)

    await coordinator.async_setup()
    await hass.async_block_till_done()

    assert coordinator.available is False
    assert coordinator._reconnect_unsub is not None

    await coordinator.async_unload()
