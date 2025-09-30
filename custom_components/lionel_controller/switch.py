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
        LionelTrainSmokeSwitch(coordinator, name),
        LionelTrainCabLightsSwitch(coordinator, name),
        LionelTrainNumberBoardsSwitch(coordinator, name),
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


class LionelTrainSmokeSwitch(LionelTrainSwitchBase):
    """Switch for controlling smoke unit."""

    _attr_name = "Smoke Unit"
    _attr_icon = "mdi:smoke"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the smoke switch."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_smoke"

    @property
    def is_on(self) -> bool:
        """Return True if the smoke unit is on."""
        return self._coordinator.smoke_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the smoke unit."""
        await self._coordinator.async_set_smoke(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the smoke unit."""
        await self._coordinator.async_set_smoke(False)
        self.async_write_ha_state()


class LionelTrainCabLightsSwitch(LionelTrainSwitchBase):
    """Switch for controlling cab lights."""

    _attr_name = "Cab Lights"
    _attr_icon = "mdi:lightbulb-outline"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the cab lights switch."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_cab_lights"

    @property
    def is_on(self) -> bool:
        """Return True if the cab lights are on."""
        return self._coordinator.cab_lights_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the cab lights."""
        await self._coordinator.async_set_cab_lights(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the cab lights."""
        await self._coordinator.async_set_cab_lights(False)
        self.async_write_ha_state()


class LionelTrainNumberBoardsSwitch(LionelTrainSwitchBase):
    """Switch for controlling number board lights."""

    _attr_name = "Number Boards"
    _attr_icon = "mdi:numeric"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the number boards switch."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_number_boards"

    @property
    def is_on(self) -> bool:
        """Return True if the number boards are on."""
        return self._coordinator.number_boards_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the number boards."""
        await self._coordinator.async_set_number_boards(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the number boards."""
        await self._coordinator.async_set_number_boards(False)
        self.async_write_ha_state()