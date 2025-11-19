"""Select entities for Candy Bianca programs."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    PROGRAM_PRESETS,
    SPIN_OPTIONS,
    TEMPERATURE_OPTIONS,
)
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

    async_add_entities(
        [
            CandyProgramPresetSelect(coordinator, entry),
            CandyTemperatureSelect(coordinator, entry),
            CandySpinSelect(coordinator, entry),
        ]
    )


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


class CandyTemperatureSelect(CandyBaseSelect):
    """Select entity to change target temperature."""

    _attr_icon = "mdi:thermometer"
    _attr_translation_key = "temperature_select"

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "temperature_select", "Temperature")
        self._attr_options = [str(value) for value in TEMPERATURE_OPTIONS]
        self._attr_current_option = self._extract_option()

    def _extract_option(self) -> str | None:
        value = self.coordinator.data.get("Temp")
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            return None

        option = str(value_int)
        return option if option in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        params = f"Write=1&TmpTgt={int(option)}"
        try:
            await self._async_call_http(params)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Error setting temperature %s on %s: %s", option, self._host, err)
            raise

        self._attr_current_option = option
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_current_option = self._extract_option()
        super()._handle_coordinator_update()


class CandySpinSelect(CandyBaseSelect):
    """Select entity to change spin speed."""

    _attr_icon = "mdi:sync-circle"
    _attr_translation_key = "spin_select"

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "spin_select", "Spin Speed")
        self._attr_options = [str(value) for value in SPIN_OPTIONS]
        self._attr_current_option = self._extract_option()

    def _extract_option(self) -> str | None:
        value = self.coordinator.data.get("SpinSp")
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            return None

        option = str(value_int)
        return option if option in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        params = f"Write=1&SpdTgt={int(option)}"
        try:
            await self._async_call_http(params)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Error setting spin %s on %s: %s", option, self._host, err)
            raise

        self._attr_current_option = option
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_current_option = self._extract_option()
        super()._handle_coordinator_update()
