"""Constants for the Lionel Train Controller integration."""

DOMAIN = "lionel_controller"

# Service UUIDs
LIONCHIEF_SERVICE_UUID = "e20a39f4-73f5-4bc4-a12f-17d1ad07a961"
DEVICE_INFO_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
GENERIC_ACCESS_SERVICE_UUID = "00001800-0000-1000-8000-00805f9b34fb"

# Default service UUID (may vary by model)
DEFAULT_SERVICE_UUID = LIONCHIEF_SERVICE_UUID

# LionChief Characteristic UUIDs
WRITE_CHARACTERISTIC_UUID = "08590f7e-db05-467e-8757-72f6faeb13d4"  # LionelCommand
NOTIFY_CHARACTERISTIC_UUID = "08590f7e-db05-467e-8757-72f6faeb14d3"  # LionelData

# Device Information Characteristic UUIDs
DEVICE_NAME_CHAR_UUID = "00002a00-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_CHAR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
SERIAL_NUMBER_CHAR_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
FIRMWARE_REVISION_CHAR_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
HARDWARE_REVISION_CHAR_UUID = "00002a27-0000-1000-8000-00805f9b34fb"
SOFTWARE_REVISION_CHAR_UUID = "00002a28-0000-1000-8000-00805f9b34fb"
MANUFACTURER_NAME_CHAR_UUID = "00002a29-0000-1000-8000-00805f9b34fb"

# Command structure constants
CMD_ZERO_BYTE = 0x00  # First byte is always 0x00
CMD_CHECKSUM = 0x00   # Checksum (simplified for now)

# Command codes (second byte)
CMD_SPEED = 0x45
CMD_DIRECTION = 0x46
CMD_BELL = 0x47
CMD_HORN = 0x48
CMD_ANNOUNCEMENT = 0x4D
CMD_DISCONNECT = 0x4B
CMD_LIGHTS = 0x51
CMD_MASTER_VOLUME = 0x4B
CMD_CHUFF_VOLUME = 0x4C
CMD_SOUND_VOLUME = 0x44

# Direction values (third byte for direction commands)
DIRECTION_FORWARD = 0x01
DIRECTION_REVERSE = 0x02

# Configuration keys
CONF_MAC_ADDRESS = "mac_address"
CONF_SERVICE_UUID = "service_uuid"

# Default values
DEFAULT_NAME = "Lionel Train"
DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRY_COUNT = 3

# Enhanced announcement sounds with proper command structure
ANNOUNCEMENTS = {
    "Random": {"code": 0x00, "name": "Random"},
    "Ready to Roll": {"code": 0x01, "name": "Ready to Roll"},
    "Hey There": {"code": 0x02, "name": "Hey There"},
    "Squeaky": {"code": 0x03, "name": "Squeaky"},
    "Water and Fire": {"code": 0x04, "name": "Water and Fire"},
    "Fastest Freight": {"code": 0x05, "name": "Fastest Freight"},
    "Penna Flyer": {"code": 0x06, "name": "Penna Flyer"},
}

# Command building helper functions
def build_command(command_code: int, parameters: list[int] = None) -> list[int]:
    """Build a properly formatted Lionel command."""
    if parameters is None:
        parameters = []
    
    # Basic command structure: [0x00, command, param1, param2, ..., checksum]
    # For simplicity, checksum is 0x00 (many commands work without proper checksum)
    command = [CMD_ZERO_BYTE, command_code] + parameters
    
    # Add checksum if parameters exist, otherwise keep simple format
    if parameters:
        command.append(CMD_CHECKSUM)
    
    return command