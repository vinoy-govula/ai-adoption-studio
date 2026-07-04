"""Wizard navigation buttons."""

from __future__ import annotations

from fasthtml.common import Button, Div, FT
from fasthtml.common import *  # noqa: F403
from monsterui.all import ButtonT
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.components.htmx import operator_hx_headers


def step_nav(lead_id: str, step_id: str, *, show_next: bool = True, next_label: str = "Next →") -> FT:
    auth = operator_hx_headers()
    buttons = [
        Button(
            "← Back",
            cls=ButtonT.secondary,
            type="button",
            hx_post=f"/wizard/{lead_id}/back",
            hx_vals=f'{{"step_id":"{step_id}"}}',
            hx_target="#step-content",
            hx_swap="innerHTML",
            hx_headers=auth,
        ),
        Button(
            "Save draft",
            cls=ButtonT.ghost,
            type="button",
            hx_post=f"/wizard/{lead_id}/draft",
            hx_include=f"#step-form-{step_id}",
            hx_vals=f'{{"step_id":"{step_id}"}}',
            hx_target="#wizard-notify-msg",
            hx_swap="innerHTML",
            hx_headers=auth,
        ),
    ]
    if show_next:
        buttons.append(
            Button(
                next_label,
                cls=ButtonT.primary,
                type="button",
                hx_post=f"/wizard/{lead_id}/{step_id}",
                hx_include=f"#step-form-{step_id}",
                hx_target="#step-content",
                hx_swap="innerHTML",
                hx_headers=auth,
            )
        )
    return Div(id="wizard-notify", cls="mt-6")(
        Div(cls="flex gap-3 items-center")(*buttons),
        Div(id="wizard-notify-msg", cls="mt-2 text-green-700 text-sm"),
    )
