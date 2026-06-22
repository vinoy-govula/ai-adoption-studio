"""Wizard navigation buttons."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings


def step_nav(lead_id: str, step_id: str, *, show_next: bool = True, next_label: str = "Next →") -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    buttons = [
        Button(
            "← Back",
            cls=ButtonT.secondary,
            hx_post=f"/wizard/{lead_id}/back",
            hx_vals=f'{{"step_id":"{step_id}"}}',
            hx_target="#step-content",
            hx_swap="innerHTML",
            hx_headers=auth,
        ),
        Button(
            "Save draft",
            cls=ButtonT.ghost,
            hx_post=f"/wizard/{lead_id}/draft",
            hx_include="closest form",
            hx_vals=f'{{"step_id":"{step_id}"}}',
            hx_target="#wizard-notify",
            hx_swap="innerHTML",
            hx_headers=auth,
        ),
    ]
    if show_next:
        buttons.append(
            Button(
                next_label,
                cls=ButtonT.primary,
                type="submit",
                form=f"step-form-{step_id}",
            )
        )
    return Div(cls="flex gap-3 mt-6 items-center", id="wizard-notify")(*buttons)
