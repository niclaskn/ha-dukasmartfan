"""Tests for setting up and unloading the integration."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers import entity_registry as er

from custom_components.dukasmartfan.const import DOMAIN

from .conftest import DEVICE_ID, IP_ADDRESS, PASSWORD


async def test_setup_creates_entities(hass, client, setup_entry):
    assert setup_entry.state is ConfigEntryState.LOADED
    args = client.add_device.call_args.args
    assert args[:3] == (DEVICE_ID, PASSWORD, IP_ADDRESS)

    registry = er.async_get(hass)
    expected = {
        "fan": DEVICE_ID,
        "sensor": [
            DEVICE_ID + "_humidity",
            DEVICE_ID + "_temperature",
            DEVICE_ID + "_fan_speed",
        ],
        "binary_sensor": DEVICE_ID + "_motor_running",
    }
    assert registry.async_get_entity_id("fan", DOMAIN, expected["fan"])
    for uid in expected["sensor"]:
        assert registry.async_get_entity_id("sensor", DOMAIN, uid)
    assert registry.async_get_entity_id(
        "binary_sensor", DOMAIN, expected["binary_sensor"]
    )
    assert len(er.async_entries_for_config_entry(registry, setup_entry.entry_id)) == 5


async def test_empty_ip_uses_broadcast(hass, client, config_entry):
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry, data={**config_entry.data, "ip_address": ""}
    )
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert client.add_device.call_args.args[2] == "<broadcast>"


async def test_device_silent_retries(hass, client, config_entry):
    client.wait_for_initialize_async.return_value = False
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    client.remove_device.assert_called_once_with(DEVICE_ID)


async def test_unload_closes_client_when_last(hass, client, setup_entry):
    client.get_device_count.return_value = 0
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()
    assert setup_entry.state is ConfigEntryState.NOT_LOADED
    client.remove_device.assert_called_once_with(setup_entry.data[CONF_DEVICE_ID])
    client.close.assert_called_once()
    assert DOMAIN not in hass.data


async def test_unload_keeps_client_with_other_devices(hass, client, setup_entry):
    client.get_device_count.return_value = 1
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    client.close.assert_not_called()
    assert DOMAIN in hass.data


async def test_client_listens_on_free_port(hass, setup_entry):
    """Port 4000 stays free for the Duka One integration (the smart fan replies to the sender's port)."""
    from custom_components.dukasmartfan import DukaClient

    DukaClient.assert_called_once_with(listen_port=0)
