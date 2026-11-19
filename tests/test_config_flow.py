"""Tests for the config flow."""

import logging

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PASSWORD,
)
from homeassistant.data_entry_flow import FlowResultType

from custom_components.dukasmartfan.const import CONF_STATICIP, DOMAIN

from .conftest import DEVICE_ID, IP_ADDRESS, PASSWORD

USER_INPUT = {
    CONF_NAME: "Bathroom",
    CONF_DEVICE_ID: DEVICE_ID,
    CONF_PASSWORD: PASSWORD,
    CONF_IP_ADDRESS: "",
    CONF_STATICIP: True,
}


async def _start(hass, user_input):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], dict(user_input)
    )


async def test_success_stores_answering_ip(hass, client, caplog):
    caplog.set_level(logging.DEBUG)
    original = dict(USER_INPUT)
    result = await _start(hass, USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bathroom"
    assert result["data"][CONF_IP_ADDRESS] == IP_ADDRESS
    assert result["data"][CONF_DEVICE_ID] == DEVICE_ID
    client.validate_device.assert_called_once_with(DEVICE_ID, PASSWORD, "<broadcast>")
    assert USER_INPUT == original
    assert PASSWORD not in caplog.text


async def test_not_static_keeps_entered_ip(hass, client):
    result = await _start(
        hass, {**USER_INPUT, CONF_IP_ADDRESS: "10.0.0.9", CONF_STATICIP: False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_IP_ADDRESS] == "10.0.0.9"


async def test_cannot_connect(hass, client, caplog):
    caplog.set_level(logging.DEBUG)
    client.validate_device.return_value = None
    result = await _start(hass, USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert PASSWORD not in caplog.text


async def test_unknown_error(hass, client, caplog):
    client.validate_device.side_effect = RuntimeError("boom")
    result = await _start(hass, USER_INPUT)
    assert result["errors"] == {"base": "unknown"}
    assert PASSWORD not in caplog.text


async def test_same_device_twice_aborts(hass, client):
    first = await _start(hass, USER_INPUT)
    assert first["type"] is FlowResultType.CREATE_ENTRY
    second = await _start(hass, USER_INPUT)
    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "already_configured"
