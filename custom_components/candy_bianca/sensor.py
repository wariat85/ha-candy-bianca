from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import CandyBiancaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Candy Bianca sensors from a config entry."""
    coordinator = CandyBiancaCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    entities: list[SensorEntity] = [
        WifiStatusSensor(coordinator, entry),
        ErrorSensor(coordinator, entry),
        MachModeSensor(coordinator, entry),
        MachModeIntSensor(coordinator, entry),
        PrSensor(coordinator, entry),
        PrCodeSensor(coordinator, entry),
        SLevelSensor(coordinator, entry),
        PhaseSensor(coordinator, entry),
        ProgramSensor(coordinator, entry),
        ProgramShortSensor(coordinator, entry),
        TempSensor(coordinator, entry),
        SpinSensor(coordinator, entry),
        SteamSensor(coordinator, entry),
        DryModeSensor(coordinator, entry),
        DelaySensor(coordinator, entry),
        RemTimeSensor(coordinator, entry),
        UpdateTimeSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class CandyBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Candy Bianca sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CandyBiancaCoordinator, entry: ConfigEntry, key: str, name: str):
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

    @property
    def _data(self) -> dict:
        return self.coordinator.data or {}


class WifiStatusSensor(CandyBaseSensor):
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "wifi_status", "WiFi Status")

    @property
    def native_value(self):
        v = int(self._data.get("WiFiStatus", 99))
        return {0: "No-Wifi", 1: "Wifi"}.get(v, "Unavailable")


class ErrorSensor(CandyBaseSensor):
    _attr_icon = "mdi:washing-machine-alert"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "err", "Errors")

    @property
    def native_value(self):
        v = int(self._data.get("Err", 255))
        if v == 0:
            return "Good"
        if v == 255:
            return "Unavailable"
        return "Alert"


class MachModeSensor(CandyBaseSensor):
    _attr_icon = "mdi:washing-machine"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "machmd", "Status")

    @property
    def native_value(self):
        v = int(self._data.get("MachMd", -1))
        mapping = {
            0: "Unavailable",
            1: "Stopped",
            2: "Washing",
            3: "Unknown_3",
            4: "Paused",
            5: "Delayed",
            6: "Unknown_6",
            7: "Finished",
        }
        return mapping.get(v, "Unavailable")


class MachModeIntSensor(CandyBaseSensor):
    _attr_icon = "mdi:washing-machine"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "machmd_int", "Status (int)")

    @property
    def native_value(self):
        return int(self._data.get("MachMd", -1))


class PrSensor(CandyBaseSensor):
    _attr_icon = "mdi:numeric"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "pr", "Pr")

    @property
    def native_value(self):
        return int(self._data.get("Pr", -1))


class PrCodeSensor(CandyBaseSensor):
    _attr_icon = "mdi:numeric"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "prcode", "PrCode")

    @property
    def native_value(self):
        return int(self._data.get("PrCode", -1))


class SLevelSensor(CandyBaseSensor):
    _attr_icon = "mdi:liquid-spot"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "slevel", "Soil Level")

    @property
    def native_value(self):
        return int(self._data.get("SLevel", -1))


class PhaseSensor(CandyBaseSensor):
    _attr_icon = "mdi:state-machine"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "phase", "Phase")

    @property
    def native_value(self):
        v = int(self._data.get("PrPh", -1))
        mapping = {
            0: "Unavailable",
            1: "Prewash",
            2: "Wash",
            3: "Rinse",
            4: "End",
            5: "Drying",
            6: "Error",
            7: "Steam",
            8: "Good Night",
        }
        return mapping.get(v, "Unavailable")


class ProgramSensor(CandyBaseSensor):
    _attr_icon = "mdi:washing-machine"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "program", "Program")

    @property
    def native_value(self):
        d = self._data
        code = int(d.get("PrCode", -1))
        pr = int(d.get("Pr", -1))
        lvl = int(d.get("SLevel", -1))
        dry = int(d.get("DryT", 0))

        if code == 7 and pr == 16 and lvl == 1:
            return "Perfect Rapid 14 Min."
        if code == 7 and pr == 16 and lvl == 2:
            return "Perfect Rapid 30 Min."
        if code == 7 and pr == 16 and lvl == 3:
            return "Perfect Rapid 44 Min."
        if code == 8 and pr == 15:
            return "Perfect Rapid 59 Min."
        if code == 77 and pr == 11 and dry == 1:
            return "Asciugatura Misti (Extra Asciutto)"
        if code == 77 and pr == 11 and dry == 2:
            return "Asciugatura Misti (Pronto Stiro)"
        if code == 77 and pr == 11 and dry == 3:
            return "Asciugatura Misti (Pronto Armadio)"

        return "Other"


class ProgramShortSensor(CandyBaseSensor):
    _attr_icon = "mdi:washing-machine"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "program_short", "Program (short)")

    @property
    def native_value(self):
        d = self._data
        code = int(d.get("PrCode", -1))
        pr = int(d.get("Pr", -1))
        lvl = int(d.get("SLevel", -1))

        if code == 7 and pr == 16 and lvl == 1:
            return "Rapid 14"
        if code == 7 and pr == 16 and lvl == 2:
            return "Rapid 30"
        if code == 7 and pr == 16 and lvl == 3:
            return "Rapid 44"
        if code == 8 and pr == 15:
            return "Rapid 59"
        if code == 77 and pr == 11:
            return "Drying"

        return "Other"


class TempSensor(CandyBaseSensor):
    _attr_icon = "mdi:thermometer"
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "temp", "Temperature")

    @property
    def native_value(self):
        return int(self._data.get("Temp", 0))


class SpinSensor(CandyBaseSensor):
    _attr_icon = "mdi:cached"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "spin", "Spin Speed")

    @property
    def native_value(self):
        return int(self._data.get("SpinSp", 0))


class SteamSensor(CandyBaseSensor):
    _attr_icon = "mdi:weather-dust"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "steam", "Steam")

    @property
    def native_value(self):
        return int(self._data.get("Steam", 0))


class DryModeSensor(CandyBaseSensor):
    _attr_icon = "mdi:tumble-dryer"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "dry_mode", "Dry Mode")

    @property
    def native_value(self):
        v = int(self._data.get("DryT", 0))
        return {
            0: "None",
            1: "Extra asciutto",
            2: "Pronto stiro",
            3: "Pronto armadio",
        }.get(v, "None")


class DelaySensor(CandyBaseSensor):
    _attr_icon = "mdi:timer-sand-empty"
    _attr_native_unit_of_measurement = "h"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "delay", "Delay")

    @property
    def native_value(self):
        v = int(self._data.get("DelVal", 0))
        return v // 60


class RemTimeSensor(CandyBaseSensor):
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "remtime", "Remaining Time")

    @property
    def native_value(self):
        v = int(self._data.get("RemTime", 0))
        return v // 60 if v >= 0 else None


class UpdateTimeSensor(CandyBaseSensor):
    _attr_icon = "mdi:update"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "update_time", "Last Update")

    @property
    def native_value(self):
        ts = self.coordinator.last_update_success_time
        if isinstance(ts, datetime):
            return ts.isoformat()
        return None
