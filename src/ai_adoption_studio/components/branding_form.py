"""Branding form for playground kit."""

from __future__ import annotations

from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings


def branding_form(lead_id: str, values: dict[str, Any] | None = None) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    v = values or {}
    stage = v.get("infrastructure_stage", "playground")
    use_edge = v.get("use_edge_overlay", stage == "playground")
    default_url = v.get("public_url") or (
        "http://localhost:8000" if stage == "developer" else ""
    )

    return Form(
        id="step-form-branding_kit",
        hx_post=f"/wizard/{lead_id}/branding_kit",
        hx_target="#step-content",
        hx_swap="innerHTML",
        hx_headers=auth,
    )(
        H4("Infrastructure stage", cls="font-semibold mt-2"),
        P(
            "Select how this playground will be accessed. See deployment-catalog "
            "docs/infrastructure-journey.md for stage details.",
            cls="text-sm text-slate-600 mb-2",
        ),
        Div(cls="flex flex-col gap-2 mb-4")(
            LabelRadio(
                "Developer (localhost, no edge)",
                name="infrastructure_stage",
                value="developer",
                checked=stage == "developer",
            ),
            LabelRadio(
                "Playground (single URL, optional edge overlay)",
                name="infrastructure_stage",
                value="playground",
                checked=stage == "playground",
            ),
            LabelRadio(
                "Production preview (customer edge integration)",
                name="infrastructure_stage",
                value="production_preview",
                checked=stage == "production_preview",
            ),
        ),
        LabelCheckboxX(
            "Use optional edge overlay (Playground stage)",
            name="use_edge_overlay",
            value="true",
            checked=bool(use_edge),
        ),
        Card(
            P("Path contract:", cls="font-semibold text-sm"),
            Ul(
                Li("/healthz → Gateway"),
                Li("/api/v1/* → Gateway"),
                Li("/control-centre/* → Control Centre"),
            ),
            cls="bg-slate-50 text-sm mb-4 p-3",
        ),
        LabelInput("Client slug", name="client_slug", value=v.get("client_slug", "")),
        LabelInput("Display name", name="display_name", value=v.get("display_name", "")),
        LabelTextArea("Welcome message", name="welcome_message", value=v.get("welcome_message", "")),
        LabelInput("Logo URL", name="logo_url", value=v.get("logo_url", "")),
        LabelInput(
            "Public URL",
            name="public_url",
            value=default_url or v.get("public_url", settings.gateway_base_url),
            placeholder="https://playground-client.example.com",
        ),
        LabelInput("TTL (days)", name="ttl_days", value=str(v.get("ttl_days", 30))),
    )
