"""Config flow for Duka Smartfan integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from . import DukaData
from .const import CONF_STATICIP, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_DEVICE_ID): str,
        vol.Optional(CONF_PASSWORD, default="1111"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_IP_ADDRESS, default=""): str,
        vol.Optional(CONF_STATICIP, default=True): bool,
    }
)


def dovalidate(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate that we can reach the device and return the data to store.

    Blocking: run in the executor.
    """
    component: DukaData = hass.data.setdefault(DOMAIN, DukaData())

    ip_address = user_input.get(CONF_IP_ADDRESS) or "<broadcast>"
    device = component.client.validate_device(
        user_input[CONF_DEVICE_ID], user_input[CONF_PASSWORD], ip_address
    )
    if device is None:
        raise CannotConnect

    if user_input[CONF_STATICIP]:
        # Store the address the device actually answered from.
        ip_address = device.ip_address
    return {
        CONF_NAME: user_input[CONF_NAME],
        CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
        CONF_PASSWORD: user_input[CONF_PASSWORD],
        CONF_IP_ADDRESS: ip_address,
        CONF_STATICIP: user_input[CONF_STATICIP],
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Duka Smartfan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()
            try:
                data = await self.hass.async_add_executor_job(
                    dovalidate, self.hass, user_input
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                DATA_SCHEMA, user_input
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
