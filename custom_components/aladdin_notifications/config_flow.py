from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import AladdinApiClient, AladdinAuthError, AladdinConnectionError
from .const import (
    CONF_PASSWORD,
    CONF_SCHOOL_ID,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCHOOL_ID,
    DOMAIN,
)


class AladdinNotificationsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            client = AladdinApiClient(
                self.hass,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_SCHOOL_ID],
            )
            try:
                await client.async_login()
                await client.async_get_notifications()
            except AladdinAuthError:
                errors["base"] = "invalid_auth"
            except AladdinConnectionError:
                errors["base"] = "cannot_connect"
            finally:
                await client.async_close()

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): selector.TextSelector(),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.PASSWORD
                    )
                ),
                vol.Required(
                    CONF_SCHOOL_ID, default=DEFAULT_SCHOOL_ID
                ): selector.TextSelector(),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_reauth(self, user_input=None):
        errors = {}

        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(
                self.context["entry_id"]
            )
            client = AladdinApiClient(
                self.hass,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input.get(
                    CONF_SCHOOL_ID,
                    entry.data.get(CONF_SCHOOL_ID, DEFAULT_SCHOOL_ID),
                ),
            )
            try:
                await client.async_login()
                await client.async_get_notifications()
            except AladdinAuthError:
                errors["base"] = "invalid_auth"
            except AladdinConnectionError:
                errors["base"] = "cannot_connect"
            finally:
                await client.async_close()

            if not errors:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): selector.TextSelector(),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.PASSWORD
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="reauth", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AladdinNotificationsOptionsFlow(config_entry)


class AladdinNotificationsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
