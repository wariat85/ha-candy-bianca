from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEFAULT_NAME, PROGRAM_PRESETS
from .coordinator import CandyBiancaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Candy Bianca buttons."""
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

    entities = [
        CandyBiancaStartButton(coordinator, entry, data),
        CandyBiancaStopButton(coordinator, entry),
    ]
    async_add_entities(entities)


class CandyBiancaBaseButton(ButtonEntity):
    """Base button for Candy Bianca."""

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry, key: str, name: str, icon: str):
        self._host = coordinator.host
        self._attr_unique_id = f"{self._host}_{key}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._host)},
            name=f"{DEFAULT_NAME} ({self._host})",
            manufacturer="Candy",
            model="Bianca",
        )

    async def _async_call_http(self, params: str) -> None:
        url = f"http://{self._host}/http-write.json?encrypted=0&{params}"
        session = async_get_clientsession(self.hass)
        _LOGGER.debug("Candy Bianca Button HTTP: %s", url)
        try:
            async with session.get(url, timeout=10) as resp:
                resp.raise_for_status()
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Error calling Candy Bianca %s: %s", self._host, err)


class CandyBiancaStartButton(CandyBiancaBaseButton):
    """Button to start program (panel-selected settings)."""

    def __init__(self, coordinator, entry, data):
        super().__init__(coordinator, entry, "start_button", "Start Program", "mdi:play-circle-outline")
        self._entry_data = data
        self._pending = data.get("pending_options", {})

    async def async_press(self) -> None:
        program_url = ""
        if self._pending.get("program_preset"):
            program_url = PROGRAM_PRESETS.get(self._pending.get("program_preset", ""), "")
        elif self._pending.get("program_url"):
            program_url = self._pending.get("program_url", "")

        temp = self._pending.get("temperature")
        spin = self._pending.get("spin")
        delay = self._pending.get("delay")

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

        if self._entry_data.get("test_mode"):
            _LOGGER.debug("TEST mode: skipping button call to %s with params %s", self._host, params)
            self._pending.clear()
            return

        await self._async_call_http(params)
        self._pending.clear()


class CandyBiancaStopButton(CandyBiancaBaseButton):
    """Button to stop current program."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "stop_button", "Stop Program", "mdi:stop-circle-outline")

    async def async_press(self) -> None:
        await self._async_call_http("Write=1&StSt=0&DelMd=0")
