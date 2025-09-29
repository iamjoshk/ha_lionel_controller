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
    WRITE_CHARACTERISTIC_UUID,
    build_command,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SWITCH, Platform.BUTTON, Platform.BINARY_SENSOR]


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
    
    try:
        await coordinator.async_setup()
    except (BleakError, asyncio.TimeoutError) as err:
        _LOGGER.error("Failed to connect to Lionel train at %s: %s", mac_address, err)
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

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
        await self._async_connect()

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

            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.mac_address, connectable=True
            )
            
            if not ble_device:
                raise BleakError(f"Could not find Bluetooth device with address {self.mac_address}")

            try:
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

    async def _notification_handler(self, sender: int, data: bytearray) -> None:
        """Handle notifications from the train."""
        _LOGGER.debug("Received notification: %s", data.hex())
        # TODO: Parse status data when protocol is better understood

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
        async with self._lock:
            # Disconnect if currently connected
            if self._client and self._client.is_connected:
                try:
                    await self._client.disconnect()
                except BleakError:
                    pass
            
            self._connected = False
            self._client = None
            
            # Force a new connection
            try:
                await self._async_connect()
                return True
            except BleakError as err:
                _LOGGER.error("Failed to force reconnect: %s", err)
                return False