"""The Lionel Train Controller integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakClient, BleakError
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak, BluetoothChange
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CMD_BATTERY_STATUS,
    CMD_CAB_LIGHTS,
    CMD_COUPLER,
    CMD_MASTER_VOLUME,
    CMD_NUMBER_BOARDS,
    CMD_SMOKE,
    CMD_STATUS_REQUEST,
    CMD_TEMPERATURE,
    CMD_VOLTAGE,
    CONF_MAC_ADDRESS,
    CONF_SERVICE_UUID,
    DEFAULT_RETRY_COUNT,
    DEFAULT_TIMEOUT,
    DEVICE_INFO_SERVICE_UUID,
    DOMAIN,
    FIRMWARE_REVISION_CHAR_UUID,
    HARDWARE_REVISION_CHAR_UUID,
    LIONCHIEF_SERVICE_UUID,
    MANUFACTURER_NAME_CHAR_UUID,
    MODEL_NUMBER_CHAR_UUID,
    NOTIFY_CHARACTERISTIC_UUID,
    SERIAL_NUMBER_CHAR_UUID,
    SOFTWARE_REVISION_CHAR_UUID,
    SOUND_SOURCE_BELL,
    SOUND_SOURCE_ENGINE,
    SOUND_SOURCE_HORN,
    SOUND_SOURCE_SPEECH,
    WRITE_CHARACTERISTIC_UUID,
    build_command,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SWITCH, Platform.BUTTON, Platform.BINARY_SENSOR, Platform.SENSOR]


@callback
def _async_discovered_device(
    service_info: BluetoothServiceInfoBleak, change: BluetoothChange
) -> bool:
    """Check if discovered device is a Lionel LionChief locomotive."""
    if change != BluetoothChange.ADVERTISEMENT:
        return False
    
    # Check for Lionel LionChief service UUID
    lionel_service_uuid = LIONCHIEF_SERVICE_UUID.lower()
    return any(
        service_uuid.lower() == lionel_service_uuid
        for service_uuid in service_info.service_uuids
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lionel Train Controller from a config entry."""
    mac_address = entry.data[CONF_MAC_ADDRESS]
    name = entry.data[CONF_NAME]
    service_uuid = entry.data[CONF_SERVICE_UUID]

    coordinator = LionelTrainCoordinator(hass, mac_address, name, service_uuid)
    
    # Don't require initial connection - allow integration to load even if locomotive is off
    try:
        await coordinator.async_setup()
        _LOGGER.info("Successfully connected to Lionel train at %s", mac_address)
    except (BleakError, asyncio.TimeoutError) as err:
        _LOGGER.warning("Could not connect to Lionel train at %s during setup: %s", mac_address, err)
        _LOGGER.info("Integration will load anyway - train will connect when powered on")
        # Don't raise ConfigEntryNotReady - let the integration load anyway

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register services
    async def reload_integration_service(call):
        """Service to reload the integration for better reconnection."""
        entry_id = call.data.get("entry_id")
        if entry_id and entry_id in hass.data[DOMAIN]:
            _LOGGER.info("Reloading integration via service call")
            await hass.config_entries.async_reload(entry_id)
    
    # Register the service if not already registered
    if not hass.services.has_service(DOMAIN, "reload_integration"):
        hass.services.async_register(DOMAIN, "reload_integration", reload_integration_service)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

    return unload_ok


class LionelTrainCoordinator:
    """Coordinator for managing the Lionel train connection."""

    def __init__(
        self,
        hass: HomeAssistant,
        mac_address: str,
        name: str,
        service_uuid: str,
    ) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.mac_address = mac_address
        self.name = name
        self.service_uuid = service_uuid
        self._client: BleakClientWithServiceCache | None = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._retry_count = 0
        self._update_callbacks = set()
        
        # State tracking
        self._speed = 0
        self._direction_forward = True
        self._lights_on = True  # Default to on since locomotive lights are on when reconnected
        self._horn_on = False
        self._bell_on = False
        
        # Advanced feature state tracking
        self._master_volume = 5  # Default mid-range volume
        self._horn_volume = 5
        self._bell_volume = 5
        self._speech_volume = 5
        self._engine_volume = 5
        self._horn_pitch = 0
        self._bell_pitch = 0
        self._speech_pitch = 0
        self._engine_pitch = 0
        
        self._smoke_on = False
        self._cab_lights_on = False
        self._number_boards_on = False
        
        # Status monitoring
        self._battery_level = None
        self._temperature = None
        self._voltage = None
        
        # Device information
        self._model_number = None
        self._serial_number = None
        self._firmware_revision = None
        self._hardware_revision = None
        self._software_revision = None
        self._manufacturer_name = None

    @property
    def connected(self) -> bool:
        """Return True if connected to the train."""
        return self._connected and self._client is not None and self._client.is_connected

    @property
    def speed(self) -> int:
        """Return current speed (0-100)."""
        return self._speed

    @property
    def direction_forward(self) -> bool:
        """Return True if direction is forward."""
        return self._direction_forward

    @property
    def lights_on(self) -> bool:
        """Return True if lights are on."""
        return self._lights_on

    @property
    def horn_on(self) -> bool:
        """Return True if horn is on."""
        return self._horn_on

    @property
    def bell_on(self) -> bool:
        """Return True if bell is on."""
        return self._bell_on

    # Advanced feature properties
    @property
    def master_volume(self) -> int:
        """Return master volume (0-7)."""
        return self._master_volume

    @property
    def horn_volume(self) -> int:
        """Return horn volume (0-7)."""
        return self._horn_volume

    @property
    def bell_volume(self) -> int:
        """Return bell volume (0-7)."""
        return self._bell_volume

    @property
    def speech_volume(self) -> int:
        """Return speech volume (0-7)."""
        return self._speech_volume

    @property
    def engine_volume(self) -> int:
        """Return engine volume (0-7)."""
        return self._engine_volume

    @property
    def smoke_on(self) -> bool:
        """Return True if smoke unit is on."""
        return self._smoke_on

    @property
    def cab_lights_on(self) -> bool:
        """Return True if cab lights are on."""
        return self._cab_lights_on

    @property
    def number_boards_on(self) -> bool:
        """Return True if number boards are on."""
        return self._number_boards_on

    @property
    def battery_level(self) -> int | None:
        """Return battery level percentage."""
        return self._battery_level

    @property
    def temperature(self) -> float | None:
        """Return temperature in Celsius."""
        return self._temperature

    @property
    def voltage(self) -> float | None:
        """Return voltage."""
        return self._voltage

    @property
    def device_info(self) -> dict:
        """Return device information."""
        return {
            "model": self._model_number or "LionChief Locomotive",
            "manufacturer": self._manufacturer_name or "Lionel",
            "sw_version": self._software_revision or "Unknown",
            "hw_version": self._hardware_revision or "Unknown", 
            "serial_number": self._serial_number,
        }

    def add_update_callback(self, callback):
        """Add a callback to be called when the state changes."""
        self._update_callbacks.add(callback)

    def remove_update_callback(self, callback):
        """Remove a callback."""
        self._update_callbacks.discard(callback)

    def _notify_state_change(self):
        """Notify all registered callbacks of state changes."""
        for callback in self._update_callbacks:
            try:
                callback()
            except Exception as err:
                _LOGGER.error("Error calling update callback: %s", err)

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            await self._async_connect()
        except (BleakError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Initial connection failed during setup: %s", err)
            # Don't raise - let the integration load anyway
            # Connection will be attempted when entities try to communicate

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        self._connected = False

    async def _async_connect(self) -> None:
        """Connect to the train."""
        async with self._lock:
            if self._connected:
                return

            # Get a fresh BLE device reference
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.mac_address, connectable=True
            )
            
            if not ble_device:
                # Try to scan for the device if not found in cache
                _LOGGER.debug("Device not found in cache, attempting fresh lookup")
                await asyncio.sleep(0.5)  # Brief delay before retry
                ble_device = bluetooth.async_ble_device_from_address(
                    self.hass, self.mac_address, connectable=True
                )
                
            if not ble_device:
                raise BleakError(f"Could not find Bluetooth device with address {self.mac_address}")

            try:
                _LOGGER.debug("Establishing connection to %s", self.mac_address)
                self._client = await establish_connection(
                    BleakClientWithServiceCache,
                    ble_device,
                    self.mac_address,
                    max_attempts=3,
                )
                
                # Set up notification handler for status updates
                try:
                    await self._client.start_notify(
                        NOTIFY_CHARACTERISTIC_UUID, self._notification_handler
                    )
                except BleakError:
                    _LOGGER.debug("Could not set up notifications (train may not support them)")
                
                # Read device information if available
                await self._read_device_info()
                
                self._connected = True
                self._retry_count = 0
                _LOGGER.info("Connected to Lionel train at %s", self.mac_address)

            except BleakError as err:
                _LOGGER.error("Failed to connect to train: %s", err)
                self._connected = False
                raise
                
                self._connected = True
                self._retry_count = 0
                _LOGGER.info("Connected to Lionel train at %s", self.mac_address)

            except BleakError as err:
                _LOGGER.error("Failed to connect to train: %s", err)
                self._connected = False
                raise

    async def _notification_handler(self, sender: int, data: bytearray) -> None:
        """Handle notifications from the train."""
        _LOGGER.debug("Received notification: %s", data.hex())
        
        # Parse locomotive status data based on protocol analysis
        if len(data) >= 8 and data[0] == 0x00 and data[1] == 0x81 and data[2] == 0x02:
            # This is train status data: [0x00, 0x81, 0x02, speed, direction, 0x03, 0x0C, flags]
            try:
                self._speed = int((data[3] / 31) * 100)  # Convert 0-31 to 0-100%
                self._direction_forward = data[4] == 0x01
                
                # Parse flags byte (data[7])
                flags = data[7]
                self._lights_on = (flags & 0x04) != 0
                self._bell_on = (flags & 0x02) != 0
                
                _LOGGER.debug("Parsed train status: speed=%d%%, forward=%s, lights=%s, bell=%s", 
                             self._speed, self._direction_forward, self._lights_on, self._bell_on)
                
                # Notify entities of state change
                self._notify_state_change()
                
            except (IndexError, ValueError) as err:
                _LOGGER.debug("Error parsing train status: %s", err)
        
        # Parse battery/voltage data (estimated protocol)
        elif len(data) >= 4 and data[0] == 0x00 and data[1] == 0x64:
            # Battery status response
            try:
                self._battery_level = data[2]  # Assume percentage
                _LOGGER.debug("Parsed battery level: %d%%", self._battery_level)
                self._notify_state_change()
            except (IndexError, ValueError) as err:
                _LOGGER.debug("Error parsing battery status: %s", err)
        
        # Parse temperature data (estimated protocol)
        elif len(data) >= 4 and data[0] == 0x00 and data[1] == 0x65:
            # Temperature response
            try:
                self._temperature = data[2] - 40  # Assume offset encoding
                _LOGGER.debug("Parsed temperature: %.1f°C", self._temperature)
                self._notify_state_change()
            except (IndexError, ValueError) as err:
                _LOGGER.debug("Error parsing temperature: %s", err)
        
        # Parse voltage data (estimated protocol)
        elif len(data) >= 5 and data[0] == 0x00 and data[1] == 0x66:
            # Voltage response
            try:
                voltage_raw = (data[2] << 8) | data[3]
                self._voltage = voltage_raw / 100.0  # Assume 0.01V resolution
                _LOGGER.debug("Parsed voltage: %.2fV", self._voltage)
                self._notify_state_change()
            except (IndexError, ValueError) as err:
                _LOGGER.debug("Error parsing voltage: %s", err)

    async def _read_device_info(self) -> None:
        """Read device information characteristics."""
        device_info_chars = {
            MODEL_NUMBER_CHAR_UUID: "_model_number",
            SERIAL_NUMBER_CHAR_UUID: "_serial_number", 
            FIRMWARE_REVISION_CHAR_UUID: "_firmware_revision",
            HARDWARE_REVISION_CHAR_UUID: "_hardware_revision",
            SOFTWARE_REVISION_CHAR_UUID: "_software_revision",
            MANUFACTURER_NAME_CHAR_UUID: "_manufacturer_name",
        }
        
        for char_uuid, attr_name in device_info_chars.items():
            try:
                result = await self._client.read_gatt_char(char_uuid)
                value = result.decode('utf-8', errors='ignore').strip()
                if value:
                    setattr(self, attr_name, value)
                    _LOGGER.debug("Read %s: %s", attr_name, value)
            except BleakError:
                _LOGGER.debug("Could not read characteristic %s", char_uuid)

    async def async_send_command(self, command_data: list[int]) -> bool:
        """Send a command to the train."""
        async with self._lock:
            # Try to connect if not connected
            if not self.connected:
                try:
                    await self._async_connect()
                except BleakError as err:
                    _LOGGER.error("Failed to connect before sending command: %s", err)
                    return False

            # Retry command sending with better error handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self._client.write_gatt_char(
                        WRITE_CHARACTERISTIC_UUID, bytearray(command_data)
                    )
                    _LOGGER.debug("Sent command: %s", command_data)
                    return True

                except BleakError as err:
                    _LOGGER.warning("Failed to send command (attempt %d/%d): %s", attempt + 1, max_retries, err)
                    self._connected = False
                    
                    # Try to reconnect on subsequent attempts
                    if attempt < max_retries - 1:
                        try:
                            await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                            await self._async_connect()
                        except BleakError:
                            _LOGGER.debug("Reconnection attempt %d failed", attempt + 1)
                            continue
                    else:
                        _LOGGER.error("Failed to send command after %d attempts: %s", max_retries, err)
                        
            return False

    async def async_set_speed(self, speed: int) -> bool:
        """Set train speed (0-100)."""
        if not 0 <= speed <= 100:
            raise ValueError("Speed must be between 0 and 100")
        
        # Convert 0-100 to 0-31 (0x00-0x1F) hex scale
        hex_speed = int((speed / 100) * 31)
        command = build_command(0x45, [hex_speed])
        
        success = await self.async_send_command(command)
        if success:
            self._speed = speed
            self._notify_state_change()
        return success

    async def async_set_direction(self, forward: bool) -> bool:
        """Set train direction."""
        direction_value = 0x01 if forward else 0x02
        command = build_command(0x46, [direction_value])
        
        success = await self.async_send_command(command)
        if success:
            self._direction_forward = forward
        return success

    async def async_set_lights(self, on: bool) -> bool:
        """Set train lights."""
        command = build_command(0x51, [0x01 if on else 0x00])
        success = await self.async_send_command(command)
        if success:
            self._lights_on = on
        return success

    async def async_set_horn(self, on: bool) -> bool:
        """Set train horn."""
        command = build_command(0x48, [0x01 if on else 0x00])
        success = await self.async_send_command(command)
        if success:
            self._horn_on = on
        return success

    async def async_set_bell(self, on: bool) -> bool:
        """Set train bell."""
        command = build_command(0x47, [0x01 if on else 0x00])
        success = await self.async_send_command(command)
        if success:
            self._bell_on = on
        return success

    async def async_play_announcement(self, announcement_code: int) -> bool:
        """Play announcement sound."""
        command = build_command(0x4D, [announcement_code, 0x00])
        return await self.async_send_command(command)

    async def async_disconnect(self) -> bool:
        """Disconnect from train."""
        command = build_command(0x4B, [0x00, 0x00])
        return await self.async_send_command(command)

    async def async_force_reconnect(self) -> bool:
        """Force reconnection to the train."""
        _LOGGER.info("Force reconnecting to Lionel train at %s", self.mac_address)
        
        # Clear connection state first - don't try to send disconnect commands
        # since the locomotive might already be disconnected/powered off
        self._connected = False
        if self._client:
            try:
                if self._client.is_connected:
                    await self._client.disconnect()
                    _LOGGER.debug("Disconnected existing client")
            except Exception as err:
                _LOGGER.debug("Error disconnecting client (expected if already disconnected): %s", err)
            finally:
                self._client = None
        
        # Wait for any existing connections to clear
        await asyncio.sleep(1.0)
        
        # Now try to establish a fresh connection
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                _LOGGER.debug("Connection attempt %d/%d", attempt + 1, max_attempts)
                
                # Get fresh device reference
                ble_device = bluetooth.async_ble_device_from_address(
                    self.hass, self.mac_address, connectable=True
                )
                
                if not ble_device:
                    if attempt < max_attempts - 1:
                        wait_time = (attempt + 1) * 1.0  # 1s, 2s, 3s, 4s delays
                        _LOGGER.debug("Device not found, waiting %s seconds before retry", wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise BleakError(f"Could not find Bluetooth device {self.mac_address}")
                
                # Establish fresh connection
                async with self._lock:
                    _LOGGER.debug("Establishing connection to %s", self.mac_address)
                    self._client = await establish_connection(
                        BleakClientWithServiceCache,
                        ble_device,
                        self.mac_address,
                        max_attempts=3,
                    )
                    
                    # Set up notification handler
                    try:
                        await self._client.start_notify(
                            NOTIFY_CHARACTERISTIC_UUID, self._notification_handler
                        )
                    except BleakError:
                        _LOGGER.debug("Could not set up notifications")
                    
                    # Read device information
                    await self._read_device_info()
                    
                    self._connected = True
                    self._retry_count = 0
                    _LOGGER.info("Successfully reconnected to train")
                    
                    # Notify all entities of the reconnection
                    self._notify_state_change()
                    return True
                    
            except BleakError as err:
                _LOGGER.debug("Connection attempt %d failed: %s", attempt + 1, err)
                if attempt < max_attempts - 1:
                    wait_time = (attempt + 1) * 2.0  # 2s, 4s, 6s, 8s delays
                    _LOGGER.debug("Waiting %s seconds before retry", wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    _LOGGER.error("Failed to reconnect after %d attempts: %s", max_attempts, err)
                    return False
                    
        return False

    # Advanced feature control methods
    async def async_set_master_volume(self, volume: int) -> bool:
        """Set master volume (0-7)."""
        if not 0 <= volume <= 7:
            raise ValueError("Volume must be between 0 and 7")
        
        command = build_command(CMD_MASTER_VOLUME, [volume])
        success = await self.async_send_command(command)
        if success:
            self._master_volume = volume
            self._notify_state_change()
        return success

    async def async_set_sound_volume(self, sound_source: int, volume: int, pitch: int = None) -> bool:
        """Set volume and optionally pitch for specific sound source."""
        if not 0 <= volume <= 7:
            raise ValueError("Volume must be between 0 and 7")
        if pitch is not None and not -2 <= pitch <= 2:
            raise ValueError("Pitch must be between -2 and 2")
        
        from .const import build_volume_command
        command = build_volume_command(sound_source, volume, pitch)
        success = await self.async_send_command(command)
        
        if success:
            # Update state tracking based on sound source
            if sound_source == SOUND_SOURCE_HORN:
                self._horn_volume = volume
                if pitch is not None:
                    self._horn_pitch = pitch
            elif sound_source == SOUND_SOURCE_BELL:
                self._bell_volume = volume
                if pitch is not None:
                    self._bell_pitch = pitch
            elif sound_source == SOUND_SOURCE_SPEECH:
                self._speech_volume = volume
                if pitch is not None:
                    self._speech_pitch = pitch
            elif sound_source == SOUND_SOURCE_ENGINE:
                self._engine_volume = volume
                if pitch is not None:
                    self._engine_pitch = pitch
            
            self._notify_state_change()
        return success

    async def async_set_smoke(self, on: bool) -> bool:
        """Set smoke unit on/off."""
        command = build_command(CMD_SMOKE, [0x01 if on else 0x00])
        success = await self.async_send_command(command)
        if success:
            self._smoke_on = on
            self._notify_state_change()
        return success

    async def async_fire_coupler(self) -> bool:
        """Fire the coupler (one-shot action)."""
        command = build_command(CMD_COUPLER, [0x01])
        return await self.async_send_command(command)

    async def async_set_cab_lights(self, on: bool) -> bool:
        """Set cab lights on/off."""
        command = build_command(CMD_CAB_LIGHTS, [0x01 if on else 0x00])
        success = await self.async_send_command(command)
        if success:
            self._cab_lights_on = on
            self._notify_state_change()
        return success

    async def async_set_number_boards(self, on: bool) -> bool:
        """Set number board lights on/off."""
        command = build_command(CMD_NUMBER_BOARDS, [0x01 if on else 0x00])
        success = await self.async_send_command(command)
        if success:
            self._number_boards_on = on
            self._notify_state_change()
        return success

    async def async_request_status(self) -> bool:
        """Request locomotive status update."""
        command = build_command(CMD_STATUS_REQUEST, [])
        return await self.async_send_command(command)

    async def async_request_battery_status(self) -> bool:
        """Request battery level status."""
        command = build_command(CMD_BATTERY_STATUS, [])
        return await self.async_send_command(command)

    async def async_request_temperature(self) -> bool:
        """Request temperature reading."""
        command = build_command(CMD_TEMPERATURE, [])
        return await self.async_send_command(command)

    async def async_request_voltage(self) -> bool:
        """Request voltage reading."""
        command = build_command(CMD_VOLTAGE, [])
        return await self.async_send_command(command)