from __future__ import annotations

"""Test mode switch for Candy Bianca."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import CandyBiancaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Candy Bianca test mode switch."""
    data = hass.data[DOMAIN][entry.entry_id]
    data.setdefault("test_mode", False)
    coordinator: CandyBiancaCoordinator = data.get("coordinator")

    if coordinator is None:
        coordinator = CandyBiancaCoordinator(hass, entry)
        hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    async_add_entities([CandyTestSwitch(coordinator, data)])


class CandyTestSwitch(SwitchEntity):
    """Switch to enable/disable test mode."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: CandyBiancaCoordinator, data: dict) -> None:
        self._host = coordinator.host
        self._entry_data = data
        self._attr_unique_id = f"{self._host}_test_mode"
        self._attr_name = "Test Mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._host)},
            name=f"{DEFAULT_NAME} ({self._host})",
            manufacturer="Candy",
            model="Bianca",
        )
        self._attr_is_on = bool(self._entry_data.get("test_mode"))

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003
        self._entry_data["test_mode"] = True
        self._attr_is_on = True
        _LOGGER.info("Candy Bianca TEST mode enabled for %s", self._host)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003
        self._entry_data["test_mode"] = False
        self._attr_is_on = False
        _LOGGER.info("Candy Bianca TEST mode disabled for %s", self._host)
        self.async_write_ha_state()
