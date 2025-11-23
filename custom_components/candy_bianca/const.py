from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "candy_bianca"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.SWITCH,
]

CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_FINISH_NOTIFICATION = "finish_notification"
CONF_SATELLITE_ENTITY = "satellite_entity"
CONF_FINISH_MESSAGE = "finish_message"
CONF_KEEP_ALIVE_INTERVAL = "keep_alive_interval"

DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_KEEP_ALIVE_INTERVAL = 1  # seconds
DEFAULT_NAME = "Candy Bianca"
DEFAULT_FINISH_MESSAGE = "La lavasciuga ha terminato il programma {program_name}"

TEMPERATURE_OPTIONS: list[int] = [0, 20, 30, 40, 60, 90]
SPIN_OPTIONS: list[int] = list(range(0, 11))

# Presets: encoded program payloads sent to the washer when starting a cycle
# (used by the start service, start button, and program preset select).
PROGRAM_PRESETS = {
    "Perfect Rapid 14 Min.": "PrNm=16&PrCode=7&PrStr=Rapido 14 Min.&SLevTgt=1&Dry=0",
    "Perfect Rapid 30 Min.": "PrNm=16&PrCode=7&PrStr=Rapido 30 Min.&SLevTgt=2&Dry=0",
    "Perfect Rapid 44 Min.": "PrNm=16&PrCode=7&PrStr=Rapido 44 Min.&SLevTgt=3&Dry=0",
    "Perfect Rapid 59 Min.": "PrNm=15&PrCode=8&PrStr=Rapido 59 Min&SLevTgt=0&Dry=0",
    "Asciugatura Misti (Extra Asciutto)": "PrNm=11&PrCode=77&PrStr=Extra Asciutto&SLevTgt=0&Dry=1",
    "Asciugatura Misti (Pronto Stiro)": "PrNm=11&PrCode=77&PrStr=Pronto Stiro&SLevTgt=0&Dry=2",
    "Asciugatura Misti (Pronto Armadio)": "PrNm=11&PrCode=77&PrStr=Pronto Armadio&SLevTgt=0&Dry=3",
    "Cotone": "PrNm=1&PrCode=65&PrStr=Cotone&SLevTgt=0&Dry=0",
    "Lana": "PrNm=4&PrCode=5&PrStr=Lana&SLevTgt=0&Dry=0",
    "Delicati": "PrNm=5&PrCode=4&PrStr=Delicati&SLevTgt=0&Dry=0",
    "Risciacquo (freddo)": "PrNm=7&PrCode=35&PrStr=Risciacquo&SLevTgt=0&Dry=0",
    "Scarico + Centrifuga": "PrNm=8&PrCode=129&PrStr=scarico e centrifuga&SLevTgt=0&Dry=0",
    "Programma Vapore (Steam/Refresh)": "PrNm=9&PrCode=17&PrStr=Vapore&SLevTgt=0&Dry=0",
}
