"""Branding form for playground kit."""

from __future__ import annotations

from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings


def branding_form(lead_id: str, values: dict[str, Any] | None = None) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    v = values or {}
    return Form(
        id="step-form-branding_kit",
        hx_post=f"/wizard/{lead_id}/branding_kit",
        hx_target="#step-content",
        hx_swap="innerHTML",
        hx_headers=auth,
    )(
        LabelInput("Client slug", name="client_slug", value=v.get("client_slug", "")),
        LabelInput("Display name", name="display_name", value=v.get("display_name", "")),
        LabelTextArea("Welcome message", name="welcome_message", value=v.get("welcome_message", "")),
        LabelInput("Logo URL", name="logo_url", value=v.get("logo_url", "")),
        LabelInput("Public URL", name="public_url", value=v.get("public_url", settings.gateway_base_url)),
        LabelInput("TTL (days)", name="ttl_days", value=str(v.get("ttl_days", 30))),
    )
