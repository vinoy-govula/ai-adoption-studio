"""Cursor assist modal panel."""

from __future__ import annotations

from fasthtml.common import Button, Div, FT, H3
from monsterui.all import Card

from ai_adoption_studio.components.htmx import operator_hx_headers


_SELECT_ACTION_SCRIPT = (
    "const panel=this.closest('[data-cursor-assist-panel]');"
    "panel.querySelectorAll('[data-cursor-assist-action]').forEach((button)=>{"
    "button.classList.remove('uk-btn-primary');"
    "button.classList.add('uk-btn-secondary');"
    "button.removeAttribute('aria-pressed');"
    "});"
    "this.classList.remove('uk-btn-secondary');"
    "this.classList.add('uk-btn-primary');"
    "this.setAttribute('aria-pressed','true');"
)

_ACTION_BUTTON_CLS = (
    "cursor-assist-action min-w-44 h-10 inline-flex items-center justify-center text-center"
)


def cursor_assist_panel(lead_id: str) -> FT:
    auth = operator_hx_headers()
    return Card(
        H3("Cursor Assist", cls="font-semibold mb-2"),
        Div(cls="flex gap-2 mb-4", data_cursor_assist_panel="true")(
            Button(
                "Certify deployment",
                cls=f"uk-btn uk-btn-primary {_ACTION_BUTTON_CLS}",
                type="button",
                hx_post=f"/api/leads/{lead_id}/cursor/certify",
                hx_target="#cursor-assist-output",
                hx_headers=auth,
                data_cursor_assist_action="certify",
                onclick=_SELECT_ACTION_SCRIPT,
            ),
            Button(
                "Draft PIR",
                cls=f"uk-btn uk-btn-secondary {_ACTION_BUTTON_CLS}",
                type="button",
                hx_post=f"/api/leads/{lead_id}/cursor/pir",
                hx_target="#cursor-assist-output",
                hx_headers=auth,
                data_cursor_assist_action="pir",
                onclick=_SELECT_ACTION_SCRIPT,
            ),
        ),
        Div(id="cursor-assist-output"),
        cls="mb-4 border-dashed",
    )
