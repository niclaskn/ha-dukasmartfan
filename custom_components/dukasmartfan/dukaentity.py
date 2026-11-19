"""Base class for Duka Smartfan entities."""

from __future__ import annotations

from duka_smartfan_sdk.device import Device
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from . import DukaConfigEntry, signal_update
from .const import DOMAIN


class DukaEntity(Entity):
    """Base of a duka entity with a reference to a device."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: DukaConfigEntry) -> None:
        self.device: Device = entry.runtime_data
        self._device_id: str = entry.data[CONF_DEVICE_ID]
        firmware = " ".join(
            str(part)
            for part in (self.device.firmware_version, self.device.firmware_date)
            if part
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Duka Ventilation",
            model=f"Type {self.device.unit_type}",
            sw_version=firmware or None,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to pushed updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_update(self._device_id), self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
