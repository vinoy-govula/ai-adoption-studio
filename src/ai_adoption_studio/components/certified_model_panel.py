"""Read-only certified model preview (assessment step)."""

from __future__ import annotations

from typing import Any

from fasthtml.common import Div, FT, H4, P
from monsterui.all import Card

from ai_adoption_studio.components.model_card_summary import model_card_summary
from ai_adoption_studio.components.parity_banner import parity_banner


def certified_model_panel(
    *,
    preset: dict[str, Any] | None,
    production: dict[str, Any] | None,
    preset_key: str,
    production_key: str,
    profile: str,
) -> FT:
    return Card(
        H4("Recommended models (certified catalog)", cls="font-semibold mb-2"),
        P(f"Assessment recommends {profile} pack.", cls="text-sm text-slate-600 mb-3"),
        Div(cls="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3")(
            Div(
                P("Lab preset", cls="text-xs font-medium text-slate-500 mb-1"),
                model_card_summary(preset or {"platform_key": preset_key}, compact=True)
                if preset
                else P(preset_key, cls="text-sm"),
            ),
            Div(
                P("Production target", cls="text-xs font-medium text-slate-500 mb-1"),
                model_card_summary(production or {"model": production_key}, compact=True)
                if production
                else P(production_key, cls="text-sm"),
            ),
        ),
        parity_banner(preset_key=preset_key, production_model=production_key),
        P("Change selections on the Playground kit step.", cls="text-xs text-slate-500 mt-2"),
        cls="mb-4",
    )
