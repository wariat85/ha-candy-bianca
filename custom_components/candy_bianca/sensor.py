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
from .programs import get_program_name, get_program_short_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Candy Bianca sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CandyBiancaCoordinator = data.get("coordinator")

    if coordinator is None:
        coordinator = CandyBiancaCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        data["coordinator"] = coordinator

    entities: list[SensorEntity] = [
        OverviewSensor(coordinator, entry),
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
    _attr_icon = "mdi:alert-circle-outline"

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
    _attr_icon = "mdi:progress-clock"

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
    _attr_icon = "mdi:playlist-check"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "program", "Program")

    @property
    def native_value(self):
        return get_program_name(self._data)


class ProgramShortSensor(CandyBaseSensor):
    _attr_icon = "mdi:playlist-edit"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "program_short", "Program (short)")

    @property
    def native_value(self):
        return get_program_short_name(self._data)


class TempSensor(CandyBaseSensor):
    _attr_icon = "mdi:thermometer"
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "temp", "Temperature")

    @property
    def native_value(self):
        return int(self._data.get("Temp", 0))


class SpinSensor(CandyBaseSensor):
    _attr_icon = "mdi:sync-circle"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "spin", "Spin Speed")

    @property
    def native_value(self):
        return int(self._data.get("SpinSp", 0))


class SteamSensor(CandyBaseSensor):
    _attr_icon = "mdi:weather-fog"

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
    _attr_icon = "mdi:timer-sand"
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


class OverviewSensor(CandyBaseSensor):
    _attr_icon = "mdi:washing-machine"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "overview", "Overview")

    @property
    def native_value(self):
        v = int(self._data.get("MachMd", -1))
        return {
            0: "Unavailable",
            1: "Stopped",
            2: "Washing",
            3: "Unknown_3",
            4: "Paused",
            5: "Delayed",
            6: "Unknown_6",
            7: "Finished",
        }.get(v, "Unavailable")

    @property
    def extra_state_attributes(self):
        wifi_status = int(self._data.get("WiFiStatus", 99))
        error_value = int(self._data.get("Err", 255))
        phase_value = int(self._data.get("PrPh", -1))
        dry_value = int(self._data.get("DryT", 0))
        last_update = self.coordinator.last_update_success_time
        remaining_time = int(self._data.get("RemTime", 0))

        return {
            "wifi_status": {0: "No-Wifi", 1: "Wifi"}.get(wifi_status, "Unavailable"),
            "error": "Good" if error_value == 0 else "Unavailable" if error_value == 255 else "Alert",
            "mach_mode_raw": int(self._data.get("MachMd", -1)),
            "program": get_program_name(self._data),
            "program_short": get_program_short_name(self._data),
            "pr": int(self._data.get("Pr", -1)),
            "pr_code": int(self._data.get("PrCode", -1)),
            "soil_level": int(self._data.get("SLevel", -1)),
            "phase": {
                0: "Unavailable",
                1: "Prewash",
                2: "Wash",
                3: "Rinse",
                4: "End",
                5: "Drying",
                6: "Error",
                7: "Steam",
                8: "Good Night",
            }.get(phase_value, "Unavailable"),
            "temperature_c": int(self._data.get("Temp", 0)),
            "spin_speed": int(self._data.get("SpinSp", 0)),
            "steam": int(self._data.get("Steam", 0)),
            "dry_mode": {
                0: "None",
                1: "Extra asciutto",
                2: "Pronto stiro",
                3: "Pronto armadio",
            }.get(dry_value, "None"),
            "delay_h": int(self._data.get("DelVal", 0)) // 60,
            "remaining_time_min": remaining_time // 60 if remaining_time >= 0 else None,
            "last_update": last_update.isoformat() if isinstance(last_update, datetime) else None,
        }
