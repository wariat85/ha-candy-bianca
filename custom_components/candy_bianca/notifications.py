"""Helpers to send notifications when the program ends."""
from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_FINISH_MESSAGE,
    CONF_FINISH_NOTIFICATION,
    CONF_SATELLITE_ENTITY,
    DEFAULT_FINISH_MESSAGE,
)
from .programs import get_program_name
from .util import safe_int

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
        self._last_mode: int | None = safe_int((coordinator.data or {}).get("MachMd"))
        self._last_program_name: str | None = None

    def _handle_coordinator_update(self) -> None:
        enabled = bool(self._options.get(CONF_FINISH_NOTIFICATION))
        satellite = self._options.get(CONF_SATELLITE_ENTITY)
        data: dict[str, Any] = self._coordinator.data or {}

        current_mode = safe_int(data.get("MachMd"))
        previous_mode = self._last_mode
        self._last_mode = current_mode

        program_name = get_program_name(data)
        if program_name != "Other":
            self._last_program_name = program_name
        elif current_mode in (-1, 0):
            # Reset when the machine is idle/standby to avoid reusing stale names
            self._last_program_name = None

        if not enabled or not satellite:
            return

        if current_mode != 7:
            return

        if previous_mode in (None, 7, -1):
            return

        if program_name == "Other" and self._last_program_name:
            program_name = self._last_program_name
        message_template: str = self._options.get(
            CONF_FINISH_MESSAGE, DEFAULT_FINISH_MESSAGE
        )
        try:
            message = message_template.format(program_name=program_name)
        except Exception:  # noqa: BLE001
            message = DEFAULT_FINISH_MESSAGE.format(program_name=program_name)
        self._hass.async_create_task(self._async_send_notification(satellite, message))

    async def _async_send_notification(self, satellite: str, message: str) -> None:
        try:
            await self._hass.services.async_call(
                "assist_satellite",
                "send_text",
                {"entity_id": satellite, "text": message},
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.warning(
                "Unable to send finish notification to %s: %s", satellite, err
            )

    def async_unload(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
