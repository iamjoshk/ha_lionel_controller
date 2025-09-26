"""Button platform for Lionel Train Controller integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LionelTrainCoordinator
from .const import ANNOUNCEMENTS, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lionel Train button platform."""
    coordinator: LionelTrainCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    
    buttons = [
        LionelTrainDisconnectButton(coordinator, name),
        LionelTrainStopButton(coordinator, name),
    ]
    
    # Add announcement buttons
    for announcement_name in ANNOUNCEMENTS:
        buttons.append(
            LionelTrainAnnouncementButton(coordinator, name, announcement_name)
        )
    
    async_add_entities(buttons, True)


class LionelTrainButtonBase(ButtonEntity):
    """Base class for Lionel Train buttons."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the button."""
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


class LionelTrainDisconnectButton(LionelTrainButtonBase):
    """Button for disconnecting from the train."""

    _attr_name = "Disconnect"
    _attr_icon = "mdi:bluetooth-off"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the disconnect button."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_disconnect"

    async def async_press(self) -> None:
        """Press the button."""
        await self._coordinator.async_disconnect()


class LionelTrainStopButton(LionelTrainButtonBase):
    """Button for stopping the train."""

    _attr_name = "Stop"
    _attr_icon = "mdi:stop"

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the stop button."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_stop"

    async def async_press(self) -> None:
        """Press the button."""
        await self._coordinator.async_set_speed(0)


class LionelTrainAnnouncementButton(LionelTrainButtonBase):
    """Button for playing announcements."""

    _attr_icon = "mdi:bullhorn-variant"

    def __init__(
        self, coordinator: LionelTrainCoordinator, device_name: str, announcement_name: str
    ) -> None:
        """Initialize the announcement button."""
        super().__init__(coordinator, device_name)
        self._announcement_name = announcement_name
        self._attr_name = f"Announcement {announcement_name}"
        self._attr_unique_id = f"{coordinator.mac_address}_announcement_{announcement_name.lower().replace(' ', '_')}"

    async def async_press(self) -> None:
        """Press the button."""
        announcement_config = ANNOUNCEMENTS[self._announcement_name]
        announcement_code = announcement_config["code"]
        await self._coordinator.async_play_announcement(announcement_code)