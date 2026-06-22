"""Validation results table."""

from __future__ import annotations

from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings


def validation_results(lead_id: str, report: dict[str, Any]) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    status = report.get("status", "unknown")
    alert_cls = AlertT.success if status == "passed" else AlertT.destructive
    rows = []
    for check in report.get("checks", []):
        failed = check.get("status") == "failed"
        row = Tr(
            Td(check.get("id", "")),
            Td(check.get("status", "")),
            Td(check.get("message", "")),
            Td(
                Button(
                    "Diagnose with Cursor",
                    cls=ButtonT.ghost,
                    hx_post=f"/api/leads/{lead_id}/cursor/troubleshoot",
                    hx_vals=f'{{"failed_check":"{check.get("id", "")}"}}',
                    hx_target="#cursor-output",
                    hx_headers=auth,
                )
                if failed
                else ""
            ),
        )
        rows.append(row)

    summary = report.get("summary", {})
    return Div(
        Alert(f"Validation status: {status}", cls=alert_cls),
        Div(cls="grid grid-cols-3 gap-4 mb-4")(
            *[Card(P(k.replace("_", " ").title(), cls="text-sm"), P(str(v), cls="font-bold")) for k, v in summary.items()]
        ),
        Table(cls="w-full text-sm")(
            Thead(Tr(Th("Check"), Th("Status"), Th("Message"), Th(""))),
            Tbody(*rows) if rows else Tbody(Tr(Td("No checks", colspan="4"))),
        ),
        Div(id="cursor-output", cls="mt-4"),
    )
