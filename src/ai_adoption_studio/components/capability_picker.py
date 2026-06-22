"""Capability picker for LLM test selection."""

from __future__ import annotations

from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings
from ai_adoption_studio.models.workflow_state import ValidationState, SmokeResult


def capability_picker(
    lead_id: str,
    capabilities: list[dict[str, Any]],
    validation: ValidationState,
    smoke: SmokeResult | None = None,
    error: str = "",
) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    if not capabilities:
        caps = [("chat", "Chat (default)")]
    else:
        caps = [
            (c.get("capability_id") or c.get("id") or "chat", c.get("name") or c.get("capability_id", "chat"))
            for c in capabilities
        ]

    smoke_alert = None
    if smoke:
        cls = AlertT.success if smoke.status == "passed" else AlertT.destructive
        smoke_alert = Alert(f"Smoke: {smoke.status} — {smoke.message}", cls=cls)

    return Form(
        id="step-form-llm_test_select",
        hx_post=f"/wizard/{lead_id}/llm_test_select",
        hx_target="#step-content",
        hx_swap="innerHTML",
        hx_headers=auth,
    )(
        Alert("Applications request capabilities, not model IDs.", cls=AlertT.info) if not error else Alert(error, cls=AlertT.destructive),
        LabelSelect("Capability", *caps, name="test_capability", selected=validation.test_capability),
        LabelTextArea("Test prompt", name="test_prompt", value=validation.test_prompt),
        smoke_alert,
        Div(cls="flex gap-2 mt-4")(
            Button("Quick smoke test", cls=ButtonT.secondary, hx_post=f"/api/leads/{lead_id}/smoke-test", hx_include="#step-form-llm_test_select", hx_target="#smoke-result", hx_swap="innerHTML", hx_headers=auth),
            Div(id="smoke-result"),
        ),
    )
