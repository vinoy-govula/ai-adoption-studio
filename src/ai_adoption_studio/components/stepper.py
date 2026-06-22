"""Vertical wizard stepper sidebar."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings


def wizard_stepper(lead_id: str, steps: list[dict[str, str]], current: str) -> FT:
    items = []
    for idx, step in enumerate(steps, start=1):
        step_id = step["id"]
        status = step["status"]
        label = step["label"]
        icon = "○"
        if status == "complete":
            icon = "✓"
        elif status == "in_progress":
            icon = "●"
        elif status == "locked":
            icon = "🔒"

        cls = "block py-2 px-3 rounded text-sm mb-1"
        if step_id == current:
            cls += " bg-slate-700 font-semibold"
        elif status == "locked":
            cls += " text-slate-500 cursor-not-allowed"
        else:
            cls += " hover:bg-slate-700"

        auth_header = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"

        if status in {"complete", "available", "in_progress"}:
            items.append(
                Button(
                    Span(f"{idx}. {icon} {label}", cls="text-left w-full"),
                    cls=cls + " w-full text-left",
                    hx_get=f"/wizard/{lead_id}/{step_id}",
                    hx_target="#step-content",
                    hx_swap="innerHTML",
                    hx_headers=auth_header,
                    aria_current="step" if step_id == current else None,
                )
            )
        else:
            items.append(Div(Span(f"{idx}. {icon} {label}"), cls=cls))

    return Aside(cls="w-56 bg-slate-900 text-white min-h-screen p-4")(
        H2("Steps", cls="text-sm font-semibold mb-4 uppercase tracking-wide text-slate-400"),
        Nav(*items),
    )
