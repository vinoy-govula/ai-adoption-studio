"""Status grid with HTMX polling."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings
from ai_adoption_studio.services.status_aggregator import StatusSnapshot


def status_grid(lead_id: str, snapshot: StatusSnapshot, *, poll: bool = True) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    attrs = {"id": "status-grid"}
    if poll:
        attrs.update(
            {
                "hx_get": f"/api/leads/{lead_id}/status",
                "hx_trigger": "every 10s",
                "hx_swap": "outerHTML",
                "hx_headers": auth,
            }
        )

    cards = []
    labels = {
        "runtime": "Runtime Manager",
        "gateway": "Gateway",
        "control_centre": "Control Centre",
        "sdk": "SDK smoke",
    }
    for key, label in labels.items():
        layer = snapshot.layers.get(key)
        if not layer:
            continue
        badge = layer.status
        cards.append(
            Card(
                H4(label, cls="font-semibold"),
                P(badge, cls="text-lg capitalize"),
                P(layer.summary, cls="text-sm text-slate-600"),
            )
        )

    banner = []
    if snapshot.overall != "healthy":
        banner.append(Alert(f"Overall: {snapshot.overall}", cls=AlertT.warning))

    return Div(**attrs)(
        *banner,
        Div(cls="grid grid-cols-2 gap-4")(*cards),
        P(f"Polled at {snapshot.polled_at}", cls="text-xs text-slate-400 mt-2"),
    )
