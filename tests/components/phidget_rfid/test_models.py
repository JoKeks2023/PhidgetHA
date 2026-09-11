"""Unit tests for the capability abstraction. No Phidget22/HA dependency."""

from __future__ import annotations

from custom_components.phidget_rfid.models import (
    CHIPSET_EM4305,
    CHIPSET_T5577,
    MODEL_1023_0,
    MODEL_1023_1,
    MODEL_1024_0B,
    MODEL_1024_1,
    MODEL_UNKNOWN,
    PROTOCOL_EM4100,
    PROTOCOL_ISO11785_FDX_B,
    PROTOCOL_PHIDGET_TAG,
    identify_model,
)


def test_1023_is_read_only():
    for model in (MODEL_1023_0, MODEL_1023_1):
        assert model.can_read
        assert not model.can_write
        assert model.write_chipsets == ()
        assert model.read_protocols == (PROTOCOL_EM4100,)


def test_1024_0b_supports_write_via_t5577_only():
    assert MODEL_1024_0B.can_write
    assert MODEL_1024_0B.write_chipsets == (CHIPSET_T5577,)
    assert set(MODEL_1024_0B.read_protocols) == {
        PROTOCOL_EM4100,
        PROTOCOL_ISO11785_FDX_B,
        PROTOCOL_PHIDGET_TAG,
    }


def test_1024_1_supports_more_than_1024_0b():
    assert MODEL_1024_1.can_write
    assert CHIPSET_EM4305 in MODEL_1024_1.write_chipsets
    assert CHIPSET_T5577 in MODEL_1024_1.write_chipsets
    assert set(MODEL_1024_0B.read_protocols) <= set(MODEL_1024_1.read_protocols)


def test_identify_model_read_write_name_without_version_defaults_to_1024_0b():
    model = identify_model(device_name="PhidgetRFID Read-Write", device_version=None)
    assert model is MODEL_1024_0B


def test_identify_model_high_version_maps_to_1024_1():
    model = identify_model(device_name="PhidgetRFID Read-Write", device_version=310)
    assert model is MODEL_1024_1


def test_identify_model_read_only_name_maps_to_1023_1():
    model = identify_model(device_name="PhidgetRFID", device_version=100)
    assert model is MODEL_1023_1
    assert not model.can_write


def test_identify_model_unknown_name_is_safe_default():
    model = identify_model(device_name="Some Other Board", device_version=1)
    assert model is MODEL_UNKNOWN
    assert not model.can_write
    assert not model.has_antenna_control
