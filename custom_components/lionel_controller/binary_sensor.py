"""Binary sensor platform for Lionel Train Controller integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LionelTrainCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lionel Train binary sensor platform."""
    coordinator: LionelTrainCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    
    async_add_entities([LionelTrainConnectionSensor(coordinator, name)], True)


class LionelTrainConnectionSensor(BinarySensorEntity):
    """Binary sensor for Lionel Train connection status."""

    _attr_has_entity_name = True
    _attr_name = "Connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the binary sensor."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_connection"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": device_name,
            **coordinator.device_info,
        }
        # Register for state updates
        self._coordinator.add_update_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        self._coordinator.remove_update_callback(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        """Return True if the train is connected."""
        return self._coordinator.connected

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True  # This sensor is always available to show connection status