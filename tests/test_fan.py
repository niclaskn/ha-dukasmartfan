"""Tests for the fan entity."""

import pytest
from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.exceptions import HomeAssistantError

from custom_components.dukasmartfan.const import DOMAIN

FAN = "fan.bathroom"


async def _call(hass, domain, service, service_domain=None):
    await hass.services.async_call(
        domain, service, {ATTR_ENTITY_ID: FAN}, blocking=True
    )


async def test_turn_on_off_and_boost(hass, client, device, setup_entry):
    await _call(hass, FAN_DOMAIN, "turn_on")
    client.turn_on.assert_called_once_with(device)
    await _call(hass, FAN_DOMAIN, "turn_off")
    client.turn_off.assert_called_once_with(device)
    await _call(hass, DOMAIN, "toggle_boost")
    client.toggle_boost.assert_called_once_with(device)


@pytest.mark.parametrize(
    ("method", "domain", "service"),
    [
        ("turn_on", FAN_DOMAIN, "turn_on"),
        ("turn_off", FAN_DOMAIN, "turn_off"),
        ("toggle_boost", DOMAIN, "toggle_boost"),
    ],
)
@pytest.mark.parametrize("error", [OSError("net down"), TimeoutError("slow")])
async def test_sdk_errors_become_ha_errors(
    hass, client, setup_entry, method, domain, service, error
):
    getattr(client, method).side_effect = error
    with pytest.raises(HomeAssistantError):
        await _call(hass, domain, service)


async def test_is_on_follows_device_setting(hass, device, setup_entry, onchange):
    # Idle in automatic mode: on, but the motor is not spinning.
    device.is_on, device.is_active = True, False
    onchange()
    await hass.async_block_till_done()
    assert hass.states.get(FAN).state == STATE_ON

    device.is_on = False
    onchange()
    await hass.async_block_till_done()
    assert hass.states.get(FAN).state == STATE_OFF


async def test_device_info(hass, setup_entry):
    from homeassistant.helpers import device_registry as dr

    (entry,) = dr.async_entries_for_config_entry(
        dr.async_get(hass), setup_entry.entry_id
    )
    assert entry.name == "Bathroom"
    assert entry.manufacturer == "Duka Ventilation"
    assert entry.model == "Type 3"
    assert entry.sw_version == "1.2 2024-01-01"
