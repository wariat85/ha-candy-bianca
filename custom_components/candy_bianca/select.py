"""Select entities for Candy Bianca programs."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME, PROGRAM_PRESETS
from .coordinator import CandyBiancaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Candy Bianca select entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CandyBiancaCoordinator = data.get("coordinator")

    if coordinator is None:
        coordinator = CandyBiancaCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        data["coordinator"] = coordinator

    async_add_entities([CandyProgramPresetSelect(coordinator, entry)])


class CandyBaseSelect(CoordinatorEntity, SelectEntity):
    """Base Select entity with shared device information."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._host = coordinator.host
        self._attr_unique_id = f"{self._host}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._host)},
            name=f"{DEFAULT_NAME} ({self._host})",
            manufacturer="Candy",
            model="Bianca",
        )

    async def _async_call_http(self, params: str) -> None:
        url = f"http://{self._host}/http-write.json?encrypted=0&{params}"
        session = async_get_clientsession(self.hass)
        _LOGGER.debug("Candy Bianca Select HTTP: %s", url)
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()


class CandyProgramPresetSelect(CandyBaseSelect):
    """Select entity exposing the known Candy Bianca programs."""

    _attr_icon = "mdi:playlist-check"
    _attr_translation_key = "program_select"

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "program_select", "Program Preset")
        self._attr_options = list(PROGRAM_PRESETS)
        self._attr_current_option = None

    async def async_select_option(self, option: str) -> None:
        program = PROGRAM_PRESETS.get(option)
        if not program:
            _LOGGER.warning("Unknown Candy Bianca program preset: %s", option)
            return

        params = "&".join(["Write=1", "StSt=1", program])
        try:
            await self._async_call_http(params)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Error starting program %s on %s: %s", option, self._host, err)
            raise

        self._attr_current_option = option
        self.async_write_ha_state()
