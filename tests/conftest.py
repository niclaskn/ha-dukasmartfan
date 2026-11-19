"""Fixtures for the Duka Smartfan tests."""

from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PASSWORD,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dukasmartfan.const import CONF_STATICIP, DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"

DEVICE_ID = "DEVICE0000000001"
PASSWORD = "s3cret-pw"
IP_ADDRESS = "192.168.1.50"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""


def make_device(**overrides) -> SimpleNamespace:
    """Create a stub SDK device."""
    values = {
        "device_id": DEVICE_ID,
        "ip_address": IP_ADDRESS,
        "is_on": True,
        "is_active": False,
        "fan_speed": 0,
        "humidity": 45,
        "temperature": 21,
        "battery_status": 0,
        "firmware_version": "1.2",
        "firmware_date": "2024-01-01",
        "unit_type": 3,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture
def device() -> SimpleNamespace:
    """Return the stub device handed out by the mocked client."""
    return make_device()


@pytest.fixture
def client(device) -> Generator[MagicMock]:
    """Patch the DukaClient built by DukaData."""
    with patch("custom_components.dukasmartfan.DukaClient") as cls:
        mock = cls.return_value
        mock.add_device.return_value = device
        mock.wait_for_initialize_async = AsyncMock(return_value=True)
        mock.validate_device.return_value = device
        mock.get_device_count.return_value = 0
        yield mock


@pytest.fixture
def onchange(client):
    """Return a function that fires the callback the integration registered."""

    def fire() -> None:
        client.add_device.call_args.args[3](client.add_device.return_value)

    return fire


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a config entry for the stub device."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Bathroom",
        unique_id=DEVICE_ID,
        data={
            CONF_NAME: "Bathroom",
            CONF_DEVICE_ID: DEVICE_ID,
            CONF_PASSWORD: PASSWORD,
            CONF_IP_ADDRESS: IP_ADDRESS,
            CONF_STATICIP: True,
        },
    )


@pytest.fixture
async def setup_entry(hass, client, config_entry):
    """Set up the config entry with the mocked client."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
