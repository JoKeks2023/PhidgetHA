"""Shared fixtures: a fake `Phidget22` package so no native library is needed."""

from __future__ import annotations

import sys
import types
from typing import ClassVar

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """pytest-homeassistant-custom-component: make custom_components loadable."""
    yield


class FakePhidgetException(Exception):
    pass


class _ProtocolMember:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"RFIDProtocol.{self.name}"


class FakeRFIDProtocol:
    EM4100 = _ProtocolMember("EM4100")
    ISO11785_FDX_B = _ProtocolMember("ISO11785_FDX_B")
    PHIDGET_TAG = _ProtocolMember("PHIDGET_TAG")


class FakeRFID:
    """Stand-in for Phidget22.Devices.RFID.RFID used in tests.

    Records every call so tests can assert on addressing/handler wiring, and
    exposes `simulate_*` helpers so tests can trigger the same code path a
    real Phidget22 native-thread callback would.
    """

    instances: ClassVar[list[FakeRFID]] = []

    # Class-level knobs a test can set before connecting.
    fail_on_open = False
    device_name = "PhidgetRFID Read-Write"
    device_version = 100
    device_serial_number = 123456

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []
        self._on_tag = None
        self._on_tag_lost = None
        self._on_attach = None
        self._on_detach = None
        self._on_error = None
        self._attached = False
        self._antenna_enabled = True
        FakeRFID.instances.append(self)

    def _record(self, name: str, *args: object) -> None:
        self.calls.append((name, args))

    def setDeviceSerialNumber(self, serial: int) -> None:
        self._record("setDeviceSerialNumber", serial)

    def setHubPort(self, port: int) -> None:
        self._record("setHubPort", port)

    def setIsHubPortDevice(self, value: bool) -> None:
        self._record("setIsHubPortDevice", value)

    def setChannel(self, channel: int) -> None:
        self._record("setChannel", channel)

    def setOnTagHandler(self, fn) -> None:
        self._on_tag = fn

    def setOnTagLostHandler(self, fn) -> None:
        self._on_tag_lost = fn

    def setOnAttachHandler(self, fn) -> None:
        self._on_attach = fn

    def setOnDetachHandler(self, fn) -> None:
        self._on_detach = fn

    def setOnErrorHandler(self, fn) -> None:
        self._on_error = fn

    def openWaitForAttachment(self, timeout_ms: int) -> None:
        self._record("openWaitForAttachment", timeout_ms)
        if self.fail_on_open:
            raise FakePhidgetException("simulated open failure")
        self._attached = True
        if self._on_attach:
            self._on_attach(self)

    def close(self) -> None:
        self._record("close")
        self._attached = False

    def getAttached(self) -> bool:
        return self._attached

    def getDeviceName(self) -> str:
        return self.device_name

    def getDeviceVersion(self) -> int:
        return self.device_version

    def getDeviceSerialNumber(self) -> int:
        return self.device_serial_number

    def write(self, tag_data: str, protocol, lock_tag: bool) -> None:
        self._record("write", tag_data, protocol, lock_tag)

    def setAntennaEnabled(self, enabled: bool) -> None:
        self._record("setAntennaEnabled", enabled)
        self._antenna_enabled = enabled

    def getAntennaEnabled(self) -> bool:
        return self._antenna_enabled

    # -- test helpers, not part of the real Phidget22 API --------------------

    def simulate_tag(self, tag: str, protocol=FakeRFIDProtocol.EM4100) -> None:
        assert self._on_tag is not None, "no tag handler registered"
        self._on_tag(self, tag, protocol)

    def simulate_tag_lost(self, tag: str) -> None:
        assert self._on_tag_lost is not None, "no tag-lost handler registered"
        self._on_tag_lost(self, tag)

    def simulate_detach(self) -> None:
        self._attached = False
        assert self._on_detach is not None, "no detach handler registered"
        self._on_detach(self)


@pytest.fixture(autouse=True)
def mock_phidget22(monkeypatch: pytest.MonkeyPatch):
    """Install a fake `Phidget22` package tree into sys.modules for the test."""
    FakeRFID.instances = []
    FakeRFID.fail_on_open = False
    FakeRFID.device_name = "PhidgetRFID Read-Write"
    FakeRFID.device_version = 100
    FakeRFID.device_serial_number = 123456

    phidget22_pkg = types.ModuleType("Phidget22")
    devices_pkg = types.ModuleType("Phidget22.Devices")
    rfid_mod = types.ModuleType("Phidget22.Devices.RFID")
    rfid_mod.RFID = FakeRFID
    exception_mod = types.ModuleType("Phidget22.PhidgetException")
    exception_mod.PhidgetException = FakePhidgetException
    protocol_mod = types.ModuleType("Phidget22.RFIDProtocol")
    protocol_mod.RFIDProtocol = FakeRFIDProtocol

    monkeypatch.setitem(sys.modules, "Phidget22", phidget22_pkg)
    monkeypatch.setitem(sys.modules, "Phidget22.Devices", devices_pkg)
    monkeypatch.setitem(sys.modules, "Phidget22.Devices.RFID", rfid_mod)
    monkeypatch.setitem(sys.modules, "Phidget22.PhidgetException", exception_mod)
    monkeypatch.setitem(sys.modules, "Phidget22.RFIDProtocol", protocol_mod)

    yield FakeRFID
