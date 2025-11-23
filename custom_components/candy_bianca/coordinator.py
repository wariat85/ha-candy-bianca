from __future__ import annotations

import logging
from datetime import timedelta
from asyncio import TimeoutError

from aiohttp import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_HOST, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class CandyBiancaCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that polls Candy Bianca washer."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.host: str = entry.data[CONF_HOST]
        scan = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Candy Bianca ({self.host})",
            update_interval=timedelta(seconds=scan),
        )
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        url = f"http://{self.host}/http-read.json?encrypted=2"
        try:
            async with self._session.get(url, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.warning("Error updating Candy Bianca %s: %s", self.host, err)
            raise

        status = data.get("statusLavatrice", {})
        if not isinstance(status, dict):
            _LOGGER.warning(
                "Unexpected response from Candy Bianca %s: %s", self.host, data
            )
            return {}

        statistics_url = f"http://{self.host}/http-getStatistics.json?encrypted=2"
        try:
            async with self._session.get(statistics_url, timeout=10) as resp:
                resp.raise_for_status()
                statistics_response = await resp.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug(
                "Error updating Candy Bianca statistics %s: %s", self.host, err
            )
        else:
            counters = statistics_response.get("statusCounters")
            if isinstance(counters, dict):
                status["statistics"] = counters
            else:
                _LOGGER.debug(
                    "Unexpected statistics response from Candy Bianca %s: %s",
                    self.host,
                    statistics_response,
                )

        return status
