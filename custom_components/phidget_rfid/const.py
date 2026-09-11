"""Constants for the Phidget RFID integration."""

from __future__ import annotations

DOMAIN = "phidget_rfid"

EVENT_TAG_DETECTED = "phidget_rfid_tag"
EVENT_TAG_LOST = "phidget_rfid_tag_lost"

CONF_SERIAL_NUMBER = "serial_number"
CONF_HUB_PORT = "hub_port"
CONF_CHANNEL = "channel"
CONF_IS_HUB_PORT_DEVICE = "is_hub_port_device"
CONF_MODEL = "model"

DEFAULT_CHANNEL = 0

# Phidget22 openWaitForAttachment timeout, milliseconds.
ATTACH_TIMEOUT_MS = 5000

# How long (seconds) a "no tag" state is held before the binary sensor flips
# back to off. The RFID channel already reports tag-lost via its own event,
# this is only a safety net for missed events.
TAG_LOST_GRACE_SECONDS = 2

MANUFACTURER = "Phidgets Inc."

ATTR_TAG_ID = "tag_id"
ATTR_PROTOCOL = "protocol"
ATTR_READER = "reader"
ATTR_SERIAL_NUMBER = "serial_number"

SERVICE_WRITE_TAG = "write_tag"
SERVICE_SET_LED = "set_led"

ATTR_TAG_DATA = "tag_data"
ATTR_PROTOCOL_NAME = "protocol"
ATTR_LOCK_TAG = "lock_tag"
ATTR_STATE = "state"

SIGNAL_UPDATE = "phidget_rfid_update_{entry_id}"

# Reconnect backoff, seconds.
RECONNECT_MIN_DELAY = 5
RECONNECT_MAX_DELAY = 300
