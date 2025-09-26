"""Switch platform for Lionel Train Controller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up the Lionel Train switch platform."""
    coordinator: LionelTrainCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    
    switches = [
        LionelTrainLightsSwitch(coordinator, name),
        LionelTrainHornSwitch(coordinator, name),
        LionelTrainBellSwitch(coordinator, name),
        LionelTrainDirectionSwitch(coordinator, name),
    ]
    
    async_add_entities(switches, True)


class LionelTrainSwitchBase(SwitchEntity):
    """Base class for Lionel Train switches."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the switch."""
        self._coordinator = coordinator
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": device_name,
            **coordinator.device_info,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected


class LionelTrainLightsSwitch(LionelTrainSwitchBase):
    """Switch for controlling train lights."""

    _attr_name = "Lights"
    _attr_icon = "mdi:lightbulb"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the lights switch."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_lights"

    @property
    def is_on(self) -> bool:
        """Return True if the lights are on."""
        return self._coordinator.lights_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the lights."""
        await self._coordinator.async_set_lights(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the lights."""
        await self._coordinator.async_set_lights(False)
        self.async_write_ha_state()


class LionelTrainHornSwitch(LionelTrainSwitchBase):
    """Switch for controlling train horn."""

    _attr_name = "Horn"
    _attr_icon = "mdi:bullhorn"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the horn switch."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_horn"

    @property
    def is_on(self) -> bool:
        """Return True if the horn is on."""
        return self._coordinator.horn_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the horn."""
        await self._coordinator.async_set_horn(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the horn."""
        await self._coordinator.async_set_horn(False)
        self.async_write_ha_state()


class LionelTrainBellSwitch(LionelTrainSwitchBase):
    """Switch for controlling train bell."""

    _attr_name = "Bell"
    _attr_icon = "mdi:bell"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the bell switch."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_bell"

    @property
    def is_on(self) -> bool:
        """Return True if the bell is on."""
        return self._coordinator.bell_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the bell."""
        await self._coordinator.async_set_bell(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the bell."""
        await self._coordinator.async_set_bell(False)
        self.async_write_ha_state()


class LionelTrainDirectionSwitch(LionelTrainSwitchBase):
    """Switch for controlling train direction."""

    _attr_name = "Direction (Forward/Reverse)"
    _attr_icon = "mdi:train"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the direction switch."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_direction"

    @property
    def is_on(self) -> bool:
        """Return True if the direction is forward."""
        return self._coordinator.direction_forward

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set direction to forward."""
        await self._coordinator.async_set_direction(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Set direction to reverse."""
        await self._coordinator.async_set_direction(False)
        self.async_write_ha_state()