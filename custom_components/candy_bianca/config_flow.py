from __future__ import annotations

from asyncio import TimeoutError

import voluptuous as vol
from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from .const import (
    CONF_FINISH_MESSAGE,
    CONF_FINISH_NOTIFICATION,
    CONF_HOST,
    CONF_SATELLITE_ENTITY,
    CONF_SCAN_INTERVAL,
    DEFAULT_FINISH_MESSAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class CandyBiancaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Candy Bianca."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        reconfigure_entry = None
        if self.source == config_entries.SOURCE_RECONFIGURE:
            entry_id = self.context.get("entry_id")
            if entry_id:
                reconfigure_entry = self.hass.config_entries.async_get_entry(entry_id)

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            scan = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            finish = user_input.get(CONF_FINISH_NOTIFICATION, False)
            finish_message = (
                user_input.get(CONF_FINISH_MESSAGE, DEFAULT_FINISH_MESSAGE)
                or DEFAULT_FINISH_MESSAGE
            ).strip()
            satellite = (user_input.get(CONF_SATELLITE_ENTITY) or "").strip()

            await self.async_set_unique_id(host)
            if reconfigure_entry:
                self._abort_if_unique_id_mismatch(reconfigure_entry)
            else:
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
                if satellite:
                    try:
                        cv.entity_id(satellite)
                    except vol.Invalid:
                        errors[CONF_SATELLITE_ENTITY] = "invalid_entity_id"

            if not errors:
                options: dict[str, object] = {
                    CONF_SCAN_INTERVAL: scan,
                    CONF_FINISH_NOTIFICATION: finish,
                    CONF_FINISH_MESSAGE: finish_message,
                }
                if satellite:
                    options[CONF_SATELLITE_ENTITY] = satellite
                if reconfigure_entry:
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data={CONF_HOST: host},
                        options=options,
                    )

                return self.async_create_entry(
                    title=f"Candy Bianca ({host})",
                    data={CONF_HOST: host},
                    options=options,
                )

        current_host = (
            user_input.get(CONF_HOST, "")
            if user_input
            else reconfigure_entry.data.get(CONF_HOST, "")
            if reconfigure_entry
            else ""
        )
        current_scan = (
            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            if user_input
            else reconfigure_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            if reconfigure_entry
            else DEFAULT_SCAN_INTERVAL
        )
        current_finish = (
            user_input.get(CONF_FINISH_NOTIFICATION, False)
            if user_input
            else reconfigure_entry.options.get(CONF_FINISH_NOTIFICATION, False)
            if reconfigure_entry
            else False
        )
        current_finish_message = (
            user_input.get(CONF_FINISH_MESSAGE, DEFAULT_FINISH_MESSAGE)
            if user_input
            else reconfigure_entry.options.get(
                CONF_FINISH_MESSAGE, DEFAULT_FINISH_MESSAGE
            )
            if reconfigure_entry
            else DEFAULT_FINISH_MESSAGE
        )
        current_satellite = (
            user_input.get(CONF_SATELLITE_ENTITY, "")
            if user_input
            else reconfigure_entry.options.get(CONF_SATELLITE_ENTITY, "")
            if reconfigure_entry
            else ""
        )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=current_scan
                ): vol.All(int, vol.Range(min=5, max=3600)),
                vol.Required(
                    CONF_FINISH_NOTIFICATION,
                    default=current_finish,
                ): bool,
                vol.Optional(
                    CONF_FINISH_MESSAGE, default=current_finish_message
                ): cv.string,
                vol.Optional(
                    CONF_SATELLITE_ENTITY,
                    default=current_satellite or None,
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["assist_satellite"])
                ),
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
        current_scan = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_notification = self.config_entry.options.get(
            CONF_FINISH_NOTIFICATION, False
        )
        current_finish_message = self.config_entry.options.get(
            CONF_FINISH_MESSAGE, DEFAULT_FINISH_MESSAGE
        )
        current_satellite = self.config_entry.options.get(CONF_SATELLITE_ENTITY, "")

        if user_input is not None:
            finish_message = (
                user_input.get(CONF_FINISH_MESSAGE, DEFAULT_FINISH_MESSAGE)
                or DEFAULT_FINISH_MESSAGE
            ).strip()
            satellite = (user_input.get(CONF_SATELLITE_ENTITY) or "").strip()
            errors: dict[str, str] = {}
            if satellite:
                try:
                    cv.entity_id(satellite)
                except vol.Invalid:
                    errors[CONF_SATELLITE_ENTITY] = "invalid_entity_id"

            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._get_options_schema(
                        current_scan,
                        current_notification,
                        current_finish_message,
                        current_satellite,
                    ),
                    errors=errors,
                )
            if not satellite:
                user_input.pop(CONF_SATELLITE_ENTITY, None)
            else:
                user_input[CONF_SATELLITE_ENTITY] = satellite
            user_input[CONF_FINISH_MESSAGE] = finish_message
            return self.async_create_entry(title="", data=user_input)

        data_schema = self._get_options_schema(
            current_scan,
            current_notification,
            current_finish_message,
            current_satellite,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors={},
        )

    def _get_options_schema(
        self,
        current_scan: int,
        current_notification: bool,
        current_finish_message: str,
        current_satellite: str,
    ) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current_scan,
                ): vol.All(int, vol.Range(min=5, max=3600)),
                vol.Required(
                    CONF_FINISH_NOTIFICATION,
                    default=current_notification,
                ): bool,
                vol.Optional(
                    CONF_FINISH_MESSAGE, default=current_finish_message
                ): cv.string,
                vol.Optional(
                    CONF_SATELLITE_ENTITY,
                    default=current_satellite or None,
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["assist_satellite"])
                ),
            }
        )
