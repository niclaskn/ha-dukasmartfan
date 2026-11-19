"""Binary sensor platform for Duka Smartfan."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DukaConfigEntry
from .dukaentity import DukaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DukaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Duka Smartfan binary sensors."""
    async_add_entities([DukaSmartfanMotorRunning(entry)])


class DukaSmartfanMotorRunning(DukaEntity, BinarySensorEntity):
    """On when the motor actually spins (rpm > 0)."""

    _attr_translation_key = "motor_running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, entry: DukaConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = self._device_id + "_motor_running"

    @property
    def is_on(self) -> bool | None:
        return self.device.is_active
