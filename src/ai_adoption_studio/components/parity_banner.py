"""Parity banner for lab preset vs production model."""

from __future__ import annotations

from fasthtml.common import FT
from monsterui.all import Alert, AlertT


def parity_banner(*, preset_key: str, production_model: str) -> FT:
    if preset_key == production_model:
        return Alert(
            "Lab preset matches production model key.",
            cls=AlertT.info,
        )
    return Alert(
        f"Parity: Lab uses {preset_key}. Production uses {production_model} on client hardware. "
        "Re-validation required on client premises.",
        cls=AlertT.warning,
    )
