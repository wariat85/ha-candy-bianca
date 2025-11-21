"""Select entities for Candy Bianca programs."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
from .programs import get_program_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Candy Bianca select entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
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
    coordinator: CandyBiancaCoordinator = data.get("coordinator")

    if coordinator is None:
        coordinator = CandyBiancaCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        data["coordinator"] = coordinator

    async_add_entities(
        [
            CandyProgramPresetSelect(coordinator, entry, data),
            CandyTemperatureSelect(coordinator, entry, data),
            CandySpinSelect(coordinator, entry, data),
        ]
    )


class CandyBaseSelect(CoordinatorEntity, SelectEntity):
    """Base Select entity with shared device information."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CandyBiancaCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        data: dict,
    ) -> None:
        super().__init__(coordinator)
        self._host = coordinator.host
        self._pending = data.get("pending_options", {})
        self._attr_unique_id = f"{self._host}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._host)},
            name=f"{DEFAULT_NAME} ({self._host})",
            manufacturer="Candy",
            model="Bianca",
        )


class CandyProgramPresetSelect(CandyBaseSelect):
    """Select entity exposing the known Candy Bianca programs."""

    _attr_icon = "mdi:playlist-check"
    _attr_translation_key = "program_select"

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry, data: dict) -> None:
        super().__init__(coordinator, entry, "program_select", "Program Preset", data)
        self._attr_options = list(PROGRAM_PRESETS)
        self._attr_current_option = self._current_from_status()

    def _current_from_status(self) -> str | None:
        program = get_program_name(self.coordinator.data)
        return program if program in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        program = PROGRAM_PRESETS.get(option)
        if not program:
            _LOGGER.warning("Unknown Candy Bianca program preset: %s", option)
            return

        self._pending["program_preset"] = option
        self._pending.pop("program_url", None)
        self._attr_current_option = option
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._pending.get("program_preset"):
            self._attr_current_option = self._pending.get("program_preset")
        else:
            self._attr_current_option = self._current_from_status()
        super()._handle_coordinator_update()


class CandyTemperatureSelect(CandyBaseSelect):
    """Select entity to change target temperature."""

    _attr_icon = "mdi:thermometer"
    _attr_translation_key = "temperature_select"

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry, data: dict) -> None:
        super().__init__(coordinator, entry, "temperature_select", "Temperature", data)
        self._attr_options = [str(value) for value in TEMPERATURE_OPTIONS]
        self._attr_current_option = self._extract_option()

    def _extract_option(self) -> str | None:
        if self._pending.get("temperature") is not None:
            option = str(int(self._pending.get("temperature", 0)))
            return option if option in self._attr_options else None

        value = self.coordinator.data.get("Temp")
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            return None

        option = str(value_int)
        return option if option in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        self._pending["temperature"] = int(option)
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

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry, data: dict) -> None:
        super().__init__(coordinator, entry, "spin_select", "Spin Speed", data)
        self._attr_options = [str(value) for value in SPIN_OPTIONS]
        self._attr_current_option = self._extract_option()

    def _extract_option(self) -> str | None:
        if self._pending.get("spin") is not None:
            option = str(int(self._pending.get("spin", 0)))
            return option if option in self._attr_options else None

        value = self.coordinator.data.get("SpinSp")
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            return None

        option = str(value_int)
        return option if option in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        self._pending["spin"] = int(option)
        self._attr_current_option = option
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_current_option = self._extract_option()
        super()._handle_coordinator_update()
