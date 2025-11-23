"""Helpers to detect the human readable program name."""
from __future__ import annotations

from typing import Any, Mapping, NamedTuple


class ProgramMapping(NamedTuple):
    """Mapping between program codes and human-readable labels."""

    code: int
    pr: int
    lvl: int | None
    dry: int | None
    full_name: str
    short_name: str


# Mappings: interpret raw status fields reported by the washer to show friendly
# names on sensors and notifications.
PROGRAM_MAPPINGS: tuple[ProgramMapping, ...] = (
    ProgramMapping(7, 16, 1, None, "Perfect Rapid 14 Min.", "Rapid 14"),
    ProgramMapping(7, 16, 2, None, "Perfect Rapid 30 Min.", "Rapid 30"),
    ProgramMapping(7, 16, 3, None, "Perfect Rapid 44 Min.", "Rapid 44"),
    ProgramMapping(8, 15, None, None, "Perfect Rapid 59 Min.", "Rapid 59"),
    ProgramMapping(77, 11, None, 1, "Asciugatura Misti (Extra Asciutto)", "Drying"),
    ProgramMapping(77, 11, None, 2, "Asciugatura Misti (Pronto Stiro)", "Drying"),
    ProgramMapping(77, 11, None, 3, "Asciugatura Misti (Pronto Armadio)", "Drying"),
    ProgramMapping(65, 1, None, None, "Cotone", "Cotone"),
    ProgramMapping(5, 4, None, None, "Lana", "Lana"),
    ProgramMapping(4, 5, None, None, "Delicati", "Delicati"),
    ProgramMapping(35, 7, None, None, "Risciacquo (freddo)", "Risciacquo"),
    ProgramMapping(129, 8, None, None, "Scarico e Centrifuga", "Scarico/Centrifuga"),
    ProgramMapping(17, 9, None, None, "Vapore", "Vapore"),
)


def get_program_name(status: Mapping[str, Any]) -> str:
    """Return the friendly program name based on raw washer fields."""
    mapping = _match_program(status)
    return mapping.full_name if mapping else "Other"


def get_program_short_name(status: Mapping[str, Any]) -> str:
    """Return the short label for the current program."""
    mapping = _match_program(status)
    return mapping.short_name if mapping else "Other"


def _match_program(status: Mapping[str, Any]) -> ProgramMapping | None:
    """Return the matching program mapping for the given status."""
    try:
        code = int(status.get("PrCode", -1))
        pr = int(status.get("Pr", -1))
        lvl = status.get("SLevel")
        dry = status.get("DryT")
        lvl_val = int(lvl) if lvl is not None else None
        dry_val = int(dry) if dry is not None else None
    except (TypeError, ValueError):
        return None

    for mapping in PROGRAM_MAPPINGS:
        if mapping.code != code or mapping.pr != pr:
            continue
        if mapping.lvl is not None and mapping.lvl != lvl_val:
            continue
        if mapping.dry is not None and mapping.dry != dry_val:
            continue
        return mapping

    return None
