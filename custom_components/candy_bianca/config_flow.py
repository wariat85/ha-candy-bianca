from __future__ import annotations

from asyncio import TimeoutError

import voluptuous as vol
from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_HOST, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL


class CandyBiancaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Candy Bianca."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            scan = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            url = f"http://{host}/http-read.json?encrypted=2"
            try:
                async with session.get(url, timeout=5) as resp:
                    if resp.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        data = await resp.json(content_type=None)
                        if "statusLavatrice" not in data:
                            errors["base"] = "cannot_connect"
            except (ClientError, TimeoutError, ValueError):
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"Candy Bianca ({host})",
                    data={CONF_HOST: host},
                    options={CONF_SCAN_INTERVAL: scan},
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(int, vol.Range(min=5, max=3600)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return CandyBiancaOptionsFlow(config_entry)


class CandyBiancaOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Candy Bianca."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current_scan,
                ): vol.All(int, vol.Range(min=5, max=3600)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors={},
        )
