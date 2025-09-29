"""Sensor platform for Lionel Train Controller integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE, UnitOfTemperature, UnitOfElectricPotential
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
    
    sensors = [
        LionelTrainBatterySensor(coordinator, name),
        LionelTrainTemperatureSensor(coordinator, name),
        LionelTrainVoltageSensor(coordinator, name),
    ]
    
    async_add_entities(sensors, True)


class LionelTrainSensorBase(SensorEntity):
    """Base class for Lionel Train sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the sensor."""
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


class LionelTrainBatterySensor(LionelTrainSensorBase):
    """Sensor for battery level monitoring."""

    _attr_name = "Battery Level"
    _attr_icon = "mdi:battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_battery_level"

    @property
    def native_value(self) -> int | None:
        """Return the current battery level."""
        return self._coordinator.battery_level


class LionelTrainTemperatureSensor(LionelTrainSensorBase):
    """Sensor for temperature monitoring."""

    _attr_name = "Temperature"
    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_temperature"

    @property
    def native_value(self) -> float | None:
        """Return the current temperature."""
        return self._coordinator.temperature


class LionelTrainVoltageSensor(LionelTrainSensorBase):
    """Sensor for voltage monitoring."""

    _attr_name = "Voltage"
    _attr_icon = "mdi:flash"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT

    def __init__(self, coordinator: LionelTrainCoordinator, device_name: str) -> None:
        """Initialize the voltage sensor."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.mac_address}_voltage"

    @property
    def native_value(self) -> float | None:
        """Return the current voltage."""
        return self._coordinator.voltage