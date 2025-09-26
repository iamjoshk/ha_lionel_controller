"""Config flow for Lionel Train Controller integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from bleak import BleakScanner
from bleak.exc import BleakError
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_MAC_ADDRESS,
    CONF_SERVICE_UUID,
    DEFAULT_NAME,
    DEFAULT_SERVICE_UUID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MAC_ADDRESS): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_SERVICE_UUID, default=DEFAULT_SERVICE_UUID): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    mac_address = data[CONF_MAC_ADDRESS]
    
    # Validate MAC address format
    if not _is_valid_mac_address(mac_address):
        raise InvalidMacAddress

    # Try to discover the device
    try:
        scanner = BleakScanner()
        devices = await scanner.discover(timeout=10.0)
        
        device_found = any(
            device.address.upper() == mac_address.upper() for device in devices
        )
        
        if not device_found:
            raise CannotConnect
            
    except BleakError as err:
        _LOGGER.exception("Error discovering Bluetooth devices")
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {
        "title": data[CONF_NAME],
        "mac_address": mac_address.upper(),
        "service_uuid": data[CONF_SERVICE_UUID],
    }


def _is_valid_mac_address(mac: str) -> bool:
    """Check if MAC address is valid."""
    parts = mac.split(":")
    if len(parts) != 6:
        return False
    
    for part in parts:
        if len(part) != 2:
            return False
        try:
            int(part, 16)
        except ValueError:
            return False
    
    return True


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lionel Train Controller."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidMacAddress:
                errors[CONF_MAC_ADDRESS] = "invalid_mac"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(info["mac_address"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data={
                    CONF_MAC_ADDRESS: info["mac_address"],
                    CONF_NAME: info["title"],
                    CONF_SERVICE_UUID: info["service_uuid"],
                })

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovered_devices[discovery_info.address] = discovery_info
        
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            discovery_info = self._discovered_devices[self.unique_id]
            return self.async_create_entry(
                title=f"Lionel Train ({discovery_info.name or discovery_info.address})",
                data={
                    CONF_MAC_ADDRESS: discovery_info.address,
                    CONF_NAME: discovery_info.name or DEFAULT_NAME,
                    CONF_SERVICE_UUID: DEFAULT_SERVICE_UUID,
                },
            )

        self._set_confirm_only()
        return self.async_show_form(step_id="bluetooth_confirm")


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidMacAddress(HomeAssistantError):
    """Error to indicate there is invalid MAC address."""