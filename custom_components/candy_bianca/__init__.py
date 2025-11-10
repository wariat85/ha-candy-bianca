from __future__ import annotations

import logging
from asyncio import TimeoutError

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS, CONF_HOST
from .coordinator import CandyBiancaCoordinator

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

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, "start"):
        _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)

    return unload_ok


def _get_host_for_entity(hass: HomeAssistant, entity_id: str) -> str | None:
    """Resolve the host from an entity belonging to this integration."""
    ent_reg = er.async_get(hass)
    entity = ent_reg.async_get(entity_id)
    if entity is None or not entity.config_entry_id:
        _LOGGER.error("Entity %s not found or has no config_entry_id", entity_id)
        return None

    entry = hass.config_entries.async_get_entry(entity.config_entry_id)
    if entry is None:
        _LOGGER.error("Config entry %s not found", entity.config_entry_id)
        return None

    host = entry.data.get(CONF_HOST)
    if not host:
        _LOGGER.error("No host in config entry %s", entry.entry_id)
        return None

    return host


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


def _register_services(hass: HomeAssistant) -> None:
    """Register start/stop services."""

    async def async_start(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        if not entity_id:
            _LOGGER.error("candy_bianca.start requires entity_id")
            return

        host = _get_host_for_entity(hass, entity_id)
        if not host:
            return

        program_url = call.data.get("program_url", "")
        temp = call.data.get("temp")
        spin = call.data.get("spin")
        delay = call.data.get("delay")

        parts = ["Write=1", "StSt=1"]
        if program_url:
            parts.append(program_url)
        if temp is not None:
            parts.append(f"TmpTgt={int(temp)}")
        if spin is not None:
            parts.append(f"SpdTgt={int(spin)}")
        if delay is not None:
            parts.append(f"DelVl={int(delay)}")

        params = "&".join(parts)
        await _async_call_http(hass, host, params)

    async def async_stop(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        if not entity_id:
            _LOGGER.error("candy_bianca.stop requires entity_id")
            return

        host = _get_host_for_entity(hass, entity_id)
        if not host:
            return

        params = "Write=1&StSt=0&DelMd=0"
        await _async_call_http(hass, host, params)

    hass.services.async_register(DOMAIN, "start", async_start)
    hass.services.async_register(DOMAIN, "stop", async_stop)
