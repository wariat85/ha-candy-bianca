from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "candy_bianca"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.SELECT]

CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_NAME = "Candy Bianca"

TEMPERATURE_OPTIONS: list[int] = [0, 20, 30, 40, 60, 90]
SPIN_OPTIONS: list[int] = list(range(0, 11))

PROGRAM_PRESETS = {
    "Perfect Rapid 14 Min.": "PrNm=16&PrCode=7&PrStr=Rapido 14 Min.&SLevTgt=1&Dry=0",
    "Perfect Rapid 30 Min.": "PrNm=16&PrCode=7&PrStr=Rapido 30 Min.&SLevTgt=2&Dry=0",
    "Perfect Rapid 44 Min.": "PrNm=16&PrCode=7&PrStr=Rapido 44 Min.&SLevTgt=3&Dry=0",
    "Perfect Rapid 59 Min.": "PrNm=15&PrCode=8&PrStr=Rapido 59 Min&SLevTgt=0&Dry=0",
    "Asciugatura Misti (Extra Asciutto)": "PrNm=11&PrCode=77&PrStr=Asciuga Misti&SLevTgt=0&Dry=1",
    "Asciugatura Misti (Pronto Stiro)": "PrNm=11&PrCode=77&PrStr=Asciuga Misti&SLevTgt=0&Dry=2",
    "Asciugatura Misti (Pronto Armadio)": "PrNm=11&PrCode=77&PrStr=Asciuga Misti&SLevTgt=0&Dry=3"
}
