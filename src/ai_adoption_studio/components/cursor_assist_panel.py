"""Cursor assist modal panel."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings


def cursor_assist_panel(lead_id: str) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    return Card(
        H3("Cursor Assist", cls="font-semibold mb-2"),
        Div(cls="flex gap-2 mb-4")(
            Button(
                "Certify deployment",
                cls=ButtonT.primary,
                hx_post=f"/api/leads/{lead_id}/cursor/certify",
                hx_target="#cursor-assist-output",
                hx_headers=auth,
            ),
            Button(
                "Draft PIR",
                cls=ButtonT.secondary,
                hx_post=f"/api/leads/{lead_id}/cursor/pir",
                hx_target="#cursor-assist-output",
                hx_headers=auth,
            ),
        ),
        Div(id="cursor-assist-output"),
        cls="mb-4 border-dashed",
    )
