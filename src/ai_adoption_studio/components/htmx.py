"""Shared HTMX attribute helpers."""

from __future__ import annotations

import json

from ai_adoption_studio.config import settings


def operator_hx_headers() -> str:
    """Return valid JSON for HTMX's hx-headers attribute."""
    return json.dumps(
        {"Authorization": f"Bearer {settings.internal_api_key}"},
        separators=(",", ":"),
    )
