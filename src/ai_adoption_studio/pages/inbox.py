"""Inbox leads table."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.layouts.base import page_layout


def inbox_page(leads: list[dict], message: str = "") -> FT:
    rows = []
    for lead in leads:
        rows.append(
            Tr(
                Td(A(lead["lead_id"], href=f"/wizard/{lead['lead_id']}", cls="text-blue-600 underline")),
                Td(lead.get("org_name", "")),
                Td(lead.get("industry", "")),
                Td(Span(lead.get("pipeline_status", ""), cls="capitalize")),
                Td(lead.get("submitted_at", "")),
                Td(A("Open wizard", href=f"/wizard/{lead['lead_id']}", cls=ButtonT.primary)),
            )
        )

    return page_layout(
        "Inbox",
        "inbox",
        H1("Leads inbox", cls="text-2xl font-bold mb-4"),
        Alert(message, cls=AlertT.success) if message else "",
        Card(
            Table(cls="w-full")(
                Thead(
                    Tr(
                        Th("Lead ID"),
                        Th("Organisation"),
                        Th("Industry"),
                        Th("Status"),
                        Th("Submitted"),
                        Th("Actions"),
                    )
                ),
                Tbody(*rows) if rows else Tbody(Tr(Td("No leads yet", colspan="6"))),
            )
        ),
    )
