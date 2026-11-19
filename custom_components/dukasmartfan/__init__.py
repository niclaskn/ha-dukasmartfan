"""Duka Smartfan integration."""

from __future__ import annotations

import logging
from functools import partial

from duka_smartfan_sdk.device import Device
from duka_smartfan_sdk.dukaclient import DukaClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_IP_ADDRESS, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import dispatcher_send

from .const import DOMAIN

PLATFORMS = [
    Platform.FAN,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

_LOGGER = logging.getLogger(__name__)

type DukaConfigEntry = ConfigEntry[Device]


def signal_update(device_id: str) -> str:
    """Return the dispatcher signal used to push updates for a device."""
    return f"{DOMAIN}_update_{device_id}"


class DukaData:
    """Hold the shared Duka Smartfan client instance."""

    def __init__(self) -> None:
        self._client: DukaClient | None = None

    @property
    def client(self) -> DukaClient:
        """Get the duka smartfan client, creating it on first use."""
        if self._client is None:
            self._client = DukaClient()
        return self._client


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry) -> bool:
    """Set up Duka Smartfan from a config entry."""
    data: DukaData = hass.data.setdefault(DOMAIN, DukaData())
    client = data.client

    device_id = entry.data[CONF_DEVICE_ID]
    password = entry.data[CONF_PASSWORD]
    ip_address = entry.data.get(CONF_IP_ADDRESS) or "<broadcast>"
    _LOGGER.debug("Setting up device %s at %s", device_id, ip_address)

    def _on_change(_device: Device) -> None:
        # Called from the SDK receive thread.
        dispatcher_send(hass, signal_update(device_id))

    device = await hass.async_add_executor_job(
        partial(client.add_device, device_id, password, ip_address, _on_change)
    )
    _LOGGER.debug("Waiting for device %s to answer", device_id)
    if not await client.wait_for_initialize_async(device):
        _LOGGER.debug("Device %s did not answer", device_id)
        client.remove_device(device_id)
        raise ConfigEntryNotReady(f"Duka Smartfan {device_id} did not respond")

    entry.runtime_data = device
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Device %s set up", device_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DukaConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data: DukaData = hass.data[DOMAIN]
        client = data.client
        client.remove_device(entry.data[CONF_DEVICE_ID])
        if client.get_device_count() == 0:
            _LOGGER.debug("Last device removed, closing client")
            await hass.async_add_executor_job(client.close)
            hass.data.pop(DOMAIN, None)
    return unload_ok
