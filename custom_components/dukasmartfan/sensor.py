"""Sensor platform for Duka Smartfan."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, REVOLUTIONS_PER_MINUTE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DukaConfigEntry
from .dukaentity import DukaEntity

# The fan rpm does not trigger the SDK change callback, so it is polled.
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DukaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Duka Smartfan sensors."""
    async_add_entities(
        [
            DukaSmartfanHumidity(entry),
            DukaSmartfanTemperature(entry),
            DukaSmartfanFanSpeed(entry),
        ]
    )


class DukaSmartfanHumidity(DukaEntity, SensorEntity):
    """Humidity sensor (pushed)."""

    _attr_translation_key = "humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, entry: DukaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = self._device_id + "_humidity"

    @property
    def native_value(self) -> int | None:
        return self.device.humidity


class DukaSmartfanTemperature(DukaEntity, SensorEntity):
    """Temperature sensor (pushed)."""

    _attr_translation_key = "temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, entry: DukaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = self._device_id + "_temperature"

    @property
    def native_value(self) -> int | None:
        return self.device.temperature


class DukaSmartfanFanSpeed(DukaEntity, SensorEntity):
    """Fan speed sensor (polled, rpm changes are not pushed by the SDK)."""

    _attr_should_poll = True
    _attr_translation_key = "fan_speed"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = REVOLUTIONS_PER_MINUTE
    _attr_icon = "mdi:fan"

    def __init__(self, entry: DukaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = self._device_id + "_fan_speed"

    @property
    def native_value(self) -> int | None:
        return self.device.fan_speed
