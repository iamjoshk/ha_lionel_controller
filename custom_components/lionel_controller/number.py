"""Number platform for Lionel Train Controller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up the Lionel Train number platform."""
    coordinator: LionelTrainCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    
    async_add_entities([
        LionelTrainThrottle(coordinator, name),
        LionelTrainMasterVolume(coordinator, name),
        LionelTrainHornVolume(coordinator, name),
        LionelTrainBellVolume(coordinator, name),
        LionelTrainSpeechVolume(coordinator, name),
        LionelTrainEngineVolume(coordinator, name),
    ], True)


class LionelTrainThrottle(NumberEntity):
    """Representation of a Lionel Train throttle as a number entity."""

    _attr_has_entity_name = True
    _attr_name = "Throttle"
    _attr_icon = "mdi:train"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: LionelTrainCoordinator, name: str) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_throttle"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": name,
            **coordinator.device_info,
        }
        # Register for state updates
        self._coordinator.add_update_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        self._coordinator.remove_update_callback(self.async_write_ha_state)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected

    @property
    def native_value(self) -> float | None:
        """Return the current throttle value."""
        return self._coordinator.speed

    async def async_set_native_value(self, value: float) -> None:
        """Set the throttle value."""
        await self._coordinator.async_set_speed(int(value))
        self.async_write_ha_state()


class LionelTrainMasterVolume(NumberEntity):
    """Representation of master volume control."""

    _attr_has_entity_name = True
    _attr_name = "Master Volume"
    _attr_icon = "mdi:volume-high"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 7
    _attr_native_step = 1

    def __init__(self, coordinator: LionelTrainCoordinator, name: str) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_master_volume"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": name,
            **coordinator.device_info,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected

    @property
    def native_value(self) -> float | None:
        """Return the current master volume."""
        return self._coordinator.master_volume

    async def async_set_native_value(self, value: float) -> None:
        """Set the master volume."""
        await self._coordinator.async_set_master_volume(int(value))
        self.async_write_ha_state()


class LionelTrainHornVolume(NumberEntity):
    """Representation of horn volume control."""

    _attr_has_entity_name = True
    _attr_name = "Horn Volume"
    _attr_icon = "mdi:bullhorn"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 7
    _attr_native_step = 1

    def __init__(self, coordinator: LionelTrainCoordinator, name: str) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_horn_volume"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": name,
            **coordinator.device_info,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected

    @property
    def native_value(self) -> float | None:
        """Return the current horn volume."""
        return self._coordinator.horn_volume

    async def async_set_native_value(self, value: float) -> None:
        """Set the horn volume."""
        from .const import SOUND_SOURCE_HORN
        await self._coordinator.async_set_sound_volume(SOUND_SOURCE_HORN, int(value))
        self.async_write_ha_state()


class LionelTrainBellVolume(NumberEntity):
    """Representation of bell volume control."""

    _attr_has_entity_name = True
    _attr_name = "Bell Volume"
    _attr_icon = "mdi:bell"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 7
    _attr_native_step = 1

    def __init__(self, coordinator: LionelTrainCoordinator, name: str) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_bell_volume"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": name,
            **coordinator.device_info,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected

    @property
    def native_value(self) -> float | None:
        """Return the current bell volume."""
        return self._coordinator.bell_volume

    async def async_set_native_value(self, value: float) -> None:
        """Set the bell volume."""
        from .const import SOUND_SOURCE_BELL
        await self._coordinator.async_set_sound_volume(SOUND_SOURCE_BELL, int(value))
        self.async_write_ha_state()


class LionelTrainSpeechVolume(NumberEntity):
    """Representation of speech volume control."""

    _attr_has_entity_name = True
    _attr_name = "Speech Volume"
    _attr_icon = "mdi:account-voice"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 7
    _attr_native_step = 1

    def __init__(self, coordinator: LionelTrainCoordinator, name: str) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_speech_volume"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": name,
            **coordinator.device_info,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected

    @property
    def native_value(self) -> float | None:
        """Return the current speech volume."""
        return self._coordinator.speech_volume

    async def async_set_native_value(self, value: float) -> None:
        """Set the speech volume."""
        from .const import SOUND_SOURCE_SPEECH
        await self._coordinator.async_set_sound_volume(SOUND_SOURCE_SPEECH, int(value))
        self.async_write_ha_state()


class LionelTrainEngineVolume(NumberEntity):
    """Representation of engine volume control."""

    _attr_has_entity_name = True
    _attr_name = "Engine Volume"
    _attr_icon = "mdi:train"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 7
    _attr_native_step = 1

    def __init__(self, coordinator: LionelTrainCoordinator, name: str) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.mac_address}_engine_volume"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": name,
            **coordinator.device_info,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.connected

    @property
    def native_value(self) -> float | None:
        """Return the current engine volume."""
        return self._coordinator.engine_volume

    async def async_set_native_value(self, value: float) -> None:
        """Set the engine volume."""
        from .const import SOUND_SOURCE_ENGINE
        await self._coordinator.async_set_sound_volume(SOUND_SOURCE_ENGINE, int(value))
        self.async_write_ha_state()