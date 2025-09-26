"""Constants for the Lionel Train Controller integration."""

DOMAIN = "lionel_controller"

# Default service UUID (may vary by model)
DEFAULT_SERVICE_UUID = "e20a39f4-73f5-4bc4-a12f-17d1ad07a961"

# Characteristic UUIDs
WRITE_CHARACTERISTIC_UUID = "08590f7e-db05-467e-8757-72f6faeb13d4"
NOTIFY_CHARACTERISTIC_UUID = "08590f7e-db05-467e-8757-72f6faeb14d3"

# Command codes
CMD_SPEED = 0x45
CMD_DIRECTION = 0x46
CMD_BELL = 0x47
CMD_HORN = 0x48
CMD_ANNOUNCEMENT = 0x4D
CMD_DISCONNECT = 0x4B
CMD_LIGHTS = 0x51
CMD_VOLUME = 0x4B
CMD_CHUFF_VOLUME = 0x4C
CMD_SOUND_VOLUME = 0x44

# Direction values
DIRECTION_FORWARD = 0x01
DIRECTION_REVERSE = 0x02

# Configuration keys
CONF_MAC_ADDRESS = "mac_address"
CONF_SERVICE_UUID = "service_uuid"

# Default values
DEFAULT_NAME = "Lionel Train"
DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRY_COUNT = 3

# Announcement sounds
ANNOUNCEMENTS = {
    "Random": [0x00, 0x4D, 0x00, 0x00],
    "Ready to Roll": [0x00, 0x4D, 0x01, 0x00],
    "Hey There": [0x00, 0x4D, 0x02, 0x00],
    "Squeaky": [0x00, 0x4D, 0x03, 0x00],
    "Water and Fire": [0x00, 0x4D, 0x04, 0x00],
    "Fastest Freight": [0x00, 0x4D, 0x05, 0x00],
    "Penna Flyer": [0x00, 0x4D, 0x06, 0x00],
}