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
CMD_MASTER_VOLUME = 0x4C  # Overall volume control
CMD_SOUND_VOLUME = 0x44   # Volume/pitch for individual sound sources

# New advanced command codes
CMD_SMOKE = 0x52          # Smoke unit control (estimated)
CMD_COUPLER = 0x53        # Coupler firing (estimated)
CMD_CAB_LIGHTS = 0x54     # Cab lights control (estimated)
CMD_NUMBER_BOARDS = 0x55  # Number board lights (estimated)
CMD_STATUS_REQUEST = 0x63 # Request locomotive status
CMD_BATTERY_STATUS = 0x64 # Battery level request (estimated)
CMD_TEMPERATURE = 0x65    # Temperature reading (estimated)
CMD_VOLTAGE = 0x66        # Voltage monitoring (estimated)

# Direction values (third byte for direction commands)
DIRECTION_FORWARD = 0x01
DIRECTION_REVERSE = 0x02

# Sound source types for volume control
SOUND_SOURCE_HORN = 0x01
SOUND_SOURCE_BELL = 0x02
SOUND_SOURCE_SPEECH = 0x03
SOUND_SOURCE_ENGINE = 0x04

# Volume and pitch ranges
VOLUME_MIN = 0
VOLUME_MAX = 7
PITCH_MIN = -2
PITCH_MAX = 2

# Status monitoring constants
BATTERY_LEVEL_MIN = 0
BATTERY_LEVEL_MAX = 100
TEMPERATURE_MIN = -40
TEMPERATURE_MAX = 85
VOLTAGE_MIN = 0.0
VOLTAGE_MAX = 24.0

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
def calculate_checksum(command_code: int, parameters: list[int] = None) -> int:
    """Calculate proper Lionel checksum based on protocol."""
    if parameters is None:
        parameters = []
    
    # Checksum calculation: 0xFF - command - sum(parameters)
    checksum = 0xFF - command_code
    for param in parameters:
        checksum = (checksum - param) & 0xFF
    
    return checksum

def build_command(command_code: int, parameters: list[int] = None) -> list[int]:
    """Build a properly formatted Lionel command with correct checksum."""
    if parameters is None:
        parameters = []
    
    # Enhanced command structure: [0x00, command, param1, param2, ..., checksum]
    command = [CMD_ZERO_BYTE, command_code] + parameters
    
    # Add proper checksum
    checksum = calculate_checksum(command_code, parameters)
    command.append(checksum)
    
    return command

def build_volume_command(sound_source: int, volume: int, pitch: int = None) -> list[int]:
    """Build volume/pitch command for specific sound source."""
    if pitch is not None:
        # Clamp pitch to valid range
        pitch = max(PITCH_MIN, min(PITCH_MAX, pitch))
        return build_command(CMD_SOUND_VOLUME, [sound_source, volume, pitch & 0xFF])
    else:
        return build_command(CMD_SOUND_VOLUME, [sound_source, volume])