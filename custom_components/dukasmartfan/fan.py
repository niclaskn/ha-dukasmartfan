"""Fan platform for Duka Smartfan."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DukaConfigEntry, DukaData
from .const import DOMAIN
from .dukaentity import DukaEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DukaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Duka Smartfan fan."""
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service("toggle_boost", {}, "async_toggle_boost")
    async_add_entities([DukaSmartFanFan(hass, entry)])


class DukaSmartFanFan(DukaEntity, FanEntity):
    """A Duka Smartfan fan."""

    _attr_name = None
    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    def __init__(self, hass: HomeAssistant, entry: DukaConfigEntry) -> None:
        super().__init__(entry)
        self._data: DukaData = hass.data[DOMAIN]
        self._attr_unique_id = self._device_id

    @property
    def is_on(self) -> bool | None:
        """Return the fan's own on/off setting (not whether the motor spins)."""
        return self.device.is_on

    async def _send(self, command: Callable[..., None]) -> None:
        try:
            await self.hass.async_add_executor_job(command, self.device)
        except (OSError, TimeoutError) as err:
            raise HomeAssistantError(
                f"Could not send command to Duka Smartfan: {err}"
            ) from err

    async def async_turn_on(self, *args: Any, **kwargs: Any) -> None:
        """Turn the fan on."""
        await self._send(self._data.client.turn_on)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._send(self._data.client.turn_off)

    async def async_toggle_boost(self) -> None:
        """Toggle boost."""
        await self._send(self._data.client.toggle_boost)
