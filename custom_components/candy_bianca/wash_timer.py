"""Manage a timer entity that mirrors the washer countdown."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_TIMER_ENTITY
from .util import safe_int

_LOGGER = logging.getLogger(__name__)


class WashTimerManager:
    """Keep a Home Assistant timer in sync with the remaining time."""

    def __init__(self, hass: HomeAssistant, entry_options: dict[str, Any], coordinator) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._timer_entity: str | None = entry_options.get(CONF_TIMER_ENTITY)
        self._unsubscribe: Callable[[], None] | None = None
        self._active = False

        if self._timer_entity:
            data = coordinator.data or {}
            current_mode = safe_int(data.get("MachMd"))
            remaining_seconds = _get_remaining_seconds(data)
            self._active = _is_running(current_mode, remaining_seconds)
            self._unsubscribe = coordinator.async_add_listener(self._handle_coordinator_update)
            self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        if not self._timer_entity:
            return

        data: dict[str, Any] = self._coordinator.data or {}
        current_mode = safe_int(data.get("MachMd"))
        remaining_seconds = _get_remaining_seconds(data)

        is_running = _is_running(current_mode, remaining_seconds)

        if is_running:
            if remaining_seconds is None or remaining_seconds <= 0:
                return

            self._active = True
            self._hass.async_create_task(
                self._async_start_or_sync_timer(remaining_seconds)
            )
            return

        if not self._active:
            return

        self._active = False
        if current_mode == 7:
            self._hass.async_create_task(self._async_finish_timer())
        else:
            self._hass.async_create_task(self._async_cancel_timer())

    async def _async_start_or_sync_timer(self, remaining_seconds: int) -> None:
        payload = {
            "entity_id": self._timer_entity,
            "duration": _format_duration(remaining_seconds),
        }
        try:
            await self._hass.services.async_call(
                "timer", "start", payload, blocking=True, limit=1
            )
        except HomeAssistantError as err:
            _LOGGER.debug(
                "Unable to start/update timer %s: %s", self._timer_entity, err
            )

    async def _async_finish_timer(self) -> None:
        try:
            await self._hass.services.async_call(
                "timer", "finish", {"entity_id": self._timer_entity}, blocking=True, limit=1
            )
        except HomeAssistantError as err:
            _LOGGER.debug("Unable to finish timer %s: %s", self._timer_entity, err)

    async def _async_cancel_timer(self) -> None:
        try:
            await self._hass.services.async_call(
                "timer", "cancel", {"entity_id": self._timer_entity}, blocking=True, limit=1
            )
        except HomeAssistantError as err:
            _LOGGER.debug("Unable to cancel timer %s: %s", self._timer_entity, err)

    def async_unload(self) -> None:
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None


def _format_duration(seconds: int) -> str:
    seconds = max(0, seconds)
    total_seconds = int(timedelta(seconds=seconds).total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds_left = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_left:02d}"


def _get_remaining_seconds(data: dict[str, Any]) -> int | None:
    remaining_seconds = safe_int(data.get("RemTime"))
    if remaining_seconds < 0:
        return None
    return remaining_seconds


def _is_running(mode: int, remaining_seconds: int | None) -> bool:
    if remaining_seconds is not None and remaining_seconds > 0:
        return True
    return mode not in (0, 1, 7, -1)
