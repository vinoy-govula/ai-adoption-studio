"""Manual Control Centre checklist."""

from __future__ import annotations

from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings


def manual_checklist(lead_id: str, checks: list[dict[str, Any]], cc_url: str) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    items = []
    for check in checks:
        cid = check.get("id", "")
        complete = check.get("status") == "complete"
        items.append(
            Div(cls="mb-3")(
                LabelCheckboxX(
                    cid.replace("_", " ").title(),
                    name=cid,
                    value="complete",
                    checked=complete,
                ),
                LabelInput("Notes", name=f"{cid}_notes", value=check.get("notes", "")),
            )
        )

    return Form(
        id="step-form-manual_cc",
        hx_post=f"/wizard/{lead_id}/manual_cc",
        hx_target="#step-content",
        hx_swap="innerHTML",
        hx_headers=auth,
    )(
        A("Open Control Centre ↗", href=cc_url, target="_blank", cls="text-blue-600 underline mb-4 inline-block"),
        *items,
    )
