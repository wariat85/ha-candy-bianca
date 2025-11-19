"""Helpers to send notifications when the program ends."""
from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant

from .const import CONF_FINISH_NOTIFICATION, CONF_SATELLITE_ENTITY
from .programs import get_program_name

_LOGGER = logging.getLogger(__name__)


class FinishNotificationManager:
    """Observe coordinator updates and notify when the cycle completes."""

    def __init__(self, hass: HomeAssistant, entry_options: dict[str, Any], coordinator) -> None:
        self._hass = hass
        self._options = entry_options
        self._coordinator = coordinator
        self._unsubscribe: Callable[[], None] | None = coordinator.async_add_listener(
            self._handle_coordinator_update
        )
        self._last_mode: int | None = _safe_int((coordinator.data or {}).get("MachMd"))

    def _handle_coordinator_update(self) -> None:
        enabled = bool(self._options.get(CONF_FINISH_NOTIFICATION))
        satellite = self._options.get(CONF_SATELLITE_ENTITY)
        data: dict[str, Any] = self._coordinator.data or {}

        current_mode = _safe_int(data.get("MachMd"))
        previous_mode = self._last_mode
        self._last_mode = current_mode

        if not enabled or not satellite:
            return

        if current_mode != 7:
            return

        if previous_mode in (None, 7, -1):
            return

        program_name = get_program_name(data)
        message = f"La lavasciuga ha terminato il programma {program_name}"
        self._hass.async_create_task(self._async_send_notification(satellite, message))

    async def _async_send_notification(self, satellite: str, message: str) -> None:
        try:
            await self._hass.services.async_call(
                "assist_satellite",
                "send_text",
                {"entity_id": satellite, "text": message},
                blocking=True,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Unable to send finish notification to %s: %s", satellite, err
            )

    def async_unload(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1
