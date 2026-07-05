"""Capability picker for LLM test selection."""

from __future__ import annotations

from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.components.htmx import operator_hx_headers
from ai_adoption_studio.models.workflow_state import ValidationState, SmokeResult


def _capability_key(capability: dict[str, Any]) -> str:
    return str(
        capability.get("capability_id")
        or capability.get("id")
        or capability.get("name")
        or "summarization"
    )


def _capability_label(capability: dict[str, Any]) -> str:
    name = capability.get("name") or capability.get("capability_id") or capability.get("id")
    description = capability.get("description")
    if name and description:
        return f"{name} — {description}"
    return str(name or "summarization")


def capability_picker(
    lead_id: str,
    capabilities: list[dict[str, Any]],
    validation: ValidationState,
    smoke: SmokeResult | None = None,
    error: str = "",
) -> FT:
    auth = operator_hx_headers()
    if not capabilities:
        caps = [("summarization", "summarization — Document and text summarization")]
    else:
        caps = [(_capability_key(c), _capability_label(c)) for c in capabilities]

    cap_keys = {key for key, _ in caps}
    selected = validation.test_capability if validation.test_capability in cap_keys else caps[0][0]

    smoke_alert = None
    if smoke:
        cls = AlertT.success if smoke.status == "passed" else AlertT.error
        smoke_alert = Alert(f"Smoke: {smoke.status} — {smoke.message}", cls=cls)

    return Form(
        id="step-form-llm_test_select",
        hx_post=f"/wizard/{lead_id}/llm_test_select",
        hx_target="#step-content",
        hx_swap="innerHTML",
        hx_headers=auth,
    )(
        Input(type="hidden", name="test_capability", value=selected),
        Alert("Applications request capabilities, not model IDs.", cls=AlertT.info) if not error else Alert(error, cls=AlertT.error),
        LabelSelect("Capability", *caps, selected=selected),
        LabelTextArea("Test prompt", name="test_prompt", value=validation.test_prompt),
        smoke_alert,
        Div(cls="flex gap-2 mt-4")(
            Button(
                "Quick smoke test",
                cls=ButtonT.secondary,
                type="button",
                hx_post=f"/api/leads/{lead_id}/smoke-test",
                hx_include="#step-form-llm_test_select",
                hx_target="#smoke-result",
                hx_swap="innerHTML",
                hx_headers=auth,
            ),
            Div(id="smoke-result"),
        ),
    )
