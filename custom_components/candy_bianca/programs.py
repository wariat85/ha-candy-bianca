"""Helpers to detect the human readable program name."""
from __future__ import annotations

from typing import Mapping, Any


def get_program_name(status: Mapping[str, Any]) -> str:
    """Return the friendly program name based on raw washer fields."""
    try:
        code = int(status.get("PrCode", -1))
        pr = int(status.get("Pr", -1))
        lvl = int(status.get("SLevel", -1))
        dry = int(status.get("DryT", 0))
    except (TypeError, ValueError):
        return "Other"

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


def get_program_short_name(status: Mapping[str, Any]) -> str:
    """Return the short label for the current program."""
    try:
        code = int(status.get("PrCode", -1))
        pr = int(status.get("Pr", -1))
        lvl = int(status.get("SLevel", -1))
    except (TypeError, ValueError):
        return "Other"

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
