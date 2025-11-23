"""Utility helpers for the Candy Bianca integration."""

from __future__ import annotations

from urllib.parse import quote


def sanitize_program_url(program_url: str) -> str:
    """Encode program URL parameters while keeping readable spaces."""

    if not program_url:
        return ""

    normalized = program_url.replace("+", " ")
    return quote(normalized, safe="=&%")
