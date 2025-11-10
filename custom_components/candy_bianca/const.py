from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "candy_bianca"

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_NAME = "Candy Bianca"
