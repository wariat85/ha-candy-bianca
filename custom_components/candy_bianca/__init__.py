from __future__ import annotations

import logging
from datetime import timedelta
from asyncio import TimeoutError

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_HOST,
    CONF_KEEP_ALIVE_INTERVAL,
    DEFAULT_KEEP_ALIVE_INTERVAL,
    DOMAIN,
    PLATFORMS,
    PROGRAM_PRESETS,
)
from .coordinator import CandyBiancaCoordinator
from .notifications import FinishNotificationManager
from .wash_timer import WashTimerManager
from .util import sanitize_program_url

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """YAML setup not supported (integration is UI-based)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    data = hass.data[DOMAIN].setdefault(entry.entry_id, {})

    coordinator = CandyBiancaCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    data["coordinator"] = coordinator
    data.setdefault(
        "pending_options",
        {
            "program_preset": None,
            "program_url": None,
            "temperature": None,
            "spin": None,
            "delay": None,
        },
    )
    data.setdefault("test_mode", False)

    data["notification_manager"] = FinishNotificationManager(
        hass, entry.options, coordinator
    )
    data["timer_manager"] = WashTimerManager(hass, entry.options, coordinator)

    keep_alive_seconds = entry.options.get(
        CONF_KEEP_ALIVE_INTERVAL, DEFAULT_KEEP_ALIVE_INTERVAL
    )
    data["keep_alive_unsub"] = _setup_keep_alive(
        hass, coordinator.host, keep_alive_seconds
    )

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, "start"):
        _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        manager: FinishNotificationManager | None = entry_data.get(
            "notification_manager"
        )
        if manager:
            manager.async_unload()
        timer: WashTimerManager | None = entry_data.get("timer_manager")
        if timer:
            timer.async_unload()
        if keep_alive_unsub := entry_data.get("keep_alive_unsub"):
            keep_alive_unsub()
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)

    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _get_entry_data_for_entity(
    hass: HomeAssistant, entity_id: str
) -> tuple[str | None, ConfigEntry | None, dict | None]:
    """Resolve config entry data for an entity belonging to this integration."""
    ent_reg = er.async_get(hass)
    entity = ent_reg.async_get(entity_id)
    if entity is None or not entity.config_entry_id:
        _LOGGER.error("Entity %s not found or has no config_entry_id", entity_id)
        return None, None, None

    entry = hass.config_entries.async_get_entry(entity.config_entry_id)
    if entry is None:
        _LOGGER.error("Config entry %s not found", entity.config_entry_id)
        return None, None, None

    host = entry.data.get(CONF_HOST)
    if not host:
        _LOGGER.error("No host in config entry %s", entry.entry_id)
        return None, None, None

    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if entry_data is None:
        _LOGGER.error("No runtime data for entry %s", entry.entry_id)
        return None, None, None

    return host, entry, entry_data


async def _async_call_http(hass: HomeAssistant, host: str, params: str) -> None:
    """Send a raw HTTP command to the washer."""
    url = f"http://{host}/http-write.json?encrypted=0&{params}"
    session = async_get_clientsession(hass)
    _LOGGER.debug("Candy Bianca HTTP: %s", url)
    try:
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()
    except (ClientError, TimeoutError) as err:
        _LOGGER.error("Error calling Candy Bianca %s: %s", host, err)


def _setup_keep_alive(
    hass: HomeAssistant, host: str, keep_alive_seconds: int
):
    if keep_alive_seconds <= 0:
        return None

    session = async_get_clientsession(hass)

    async def _async_ping(_now):
        url = f"http://{host}/http-read.json?encrypted=2"
        _LOGGER.debug("Candy Bianca keep-alive: %s", url)
        try:
            async with session.get(url, timeout=5) as resp:
                resp.raise_for_status()
        except (ClientError, TimeoutError) as err:
            _LOGGER.debug("Keep-alive failed for %s: %s", host, err)

    return async_track_time_interval(
        hass, _async_ping, timedelta(seconds=keep_alive_seconds)
    )


def _register_services(hass: HomeAssistant) -> None:
    """Register start/stop services."""

    async def async_start(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        if not entity_id:
            _LOGGER.error("candy_bianca.start requires entity_id")
            return

        host, _entry, entry_data = _get_entry_data_for_entity(hass, entity_id)
        if not host or not entry_data:
            return

        pending = entry_data.get("pending_options", {})
        coordinator: CandyBiancaCoordinator | None = entry_data.get("coordinator")
        status = coordinator.data if coordinator and coordinator.data else {}

        # 1) explicit URL has priority
        program_url: str = call.data.get("program_url", "")

        # 2) otherwise use preset mapping
        if not program_url:
            preset = call.data.get("program_preset")
            if preset:
                program_url = PROGRAM_PRESETS.get(preset, "")
            elif pending.get("program_preset"):
                program_url = PROGRAM_PRESETS.get(
                    pending.get("program_preset", ""), ""
                )

        if not program_url and pending.get("program_url"):
            program_url = pending.get("program_url", "")

        program_url = sanitize_program_url(program_url)

        temp = call.data.get("temp", pending.get("temperature"))
        if temp is None:
            temp = status.get("Temp")

        spin = call.data.get("spin", pending.get("spin"))
        if spin is None:
            spin = status.get("SpinSp")

        delay = call.data.get("delay", pending.get("delay"))
        if delay is None:
            delay = status.get("DelVl")

        # Clear pending options after capturing them for this run
        pending.clear()

        parts: list[str] = ["Write=1", "StSt=1"]
        if program_url:
            parts.append(program_url)
        if temp is not None:
            parts.append(f"TmpTgt={int(temp)}")
        if spin is not None:
            parts.append(f"SpdTgt={int(spin)}")
        if delay is not None:
            parts.append(f"DelVl={int(delay)}")

        params = "&".join(parts)

        if entry_data.get("test_mode"):
            _LOGGER.debug("TEST mode: skipping call to %s with params %s", host, params)
            return

        await _async_call_http(hass, host, params)

    async def async_stop(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        if not entity_id:
            _LOGGER.error("candy_bianca.stop requires entity_id")
            return

        host, _entry, _entry_data = _get_entry_data_for_entity(hass, entity_id)
        if not host:
            return

        params = "Write=1&StSt=0&DelMd=0"
        await _async_call_http(hass, host, params)

    hass.services.async_register(DOMAIN, "start", async_start)
    hass.services.async_register(DOMAIN, "stop", async_stop)
