"""Sensor platform for Lionel Train Controller integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up the Lionel Train sensor platform."""
    coordinator: LionelTrainCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    
    async_add_entities([LionelTrainStatusSensor(coordinator, name)], True)


class LionelTrainStatusSensor(SensorEntity):
    """Sensor for Lionel Train status information."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:train"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_status"
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
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self._coordinator.last_notification_hex

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional state attributes."""
        return {
            "speed": self._coordinator.speed,
            "direction_forward": self._coordinator.direction_forward,
            "lights_on": self._coordinator.lights_on,
            "bell_on": self._coordinator.bell_on,
            "horn_on": self._coordinator.horn_on,
        }
