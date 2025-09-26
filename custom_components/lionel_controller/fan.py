"""Fan platform for Lionel Train Controller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
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
    """Set up the Lionel Train fan platform."""
    coordinator: LionelTrainCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    
    async_add_entities([LionelTrainFan(coordinator, name)], True)


class LionelTrainFan(FanEntity):
    """Representation of a Lionel Train as a fan for speed control."""

    _attr_has_entity_name = True
    _attr_name = "Speed"
    _attr_supported_features = FanEntityFeature.SET_SPEED
    _attr_speed_count = 100

    def __init__(self, coordinator: LionelTrainCoordinator, name: str) -> None:
        """Initialize the fan."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_speed"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": name,
            "manufacturer": "Lionel",
            "model": "LionChief Locomotive",
            "sw_version": "1.0",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected

    @property
    def is_on(self) -> bool:
        """Return True if the fan is on."""
        return self._coordinator.speed > 0

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        return self._coordinator.speed if self._coordinator.speed > 0 else None

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
        else:
            await self._coordinator.async_set_speed(percentage)
            self.async_write_ha_state()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        speed = percentage if percentage is not None else 10  # Default to 10% speed
        await self._coordinator.async_set_speed(speed)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self._coordinator.async_set_speed(0)
        self.async_write_ha_state()