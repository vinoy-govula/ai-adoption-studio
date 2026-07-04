"""Inbox leads table."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.layouts.base import page_layout, wizard_link


def inbox_page(leads: list[dict], message: str = "") -> FT:
    rows = []
    for lead in leads:
        rows.append(
            Tr(
                Td(wizard_link(lead["lead_id"], lead["lead_id"], cls="text-blue-600 underline")),
                Td(lead.get("org_name", "")),
                Td(lead.get("industry", "")),
                Td(Span(lead.get("pipeline_status", ""), cls="capitalize")),
                Td(lead.get("submitted_at", "")),
                Td(
                    Div(cls="flex gap-2")(
                        A("Open EOI", href=f"/eoi/{lead['lead_id']}", cls=ButtonT.secondary),
                        wizard_link("Open wizard", lead["lead_id"], cls=ButtonT.primary),
                    )
                ),
            )
        )

    return page_layout(
        "Inbox",
        "inbox",
        H1("Leads inbox", cls="text-2xl font-bold mb-4"),
        Alert(message, cls=AlertT.success) if message else "",
        Card(cls="mb-4")(
            Div(cls="flex flex-col md:flex-row md:items-end gap-4")(
                Div(cls="flex-1")(
                    H2("EOI intake", cls="font-semibold mb-1"),
                    P(
                        "Start from a blank EOI form or open an existing EOI by lead ID.",
                        cls="text-sm text-slate-600",
                    ),
                ),
                A("Start blank EOI", href="/eoi-form", cls=ButtonT.primary),
                Form(method="post", action="/eoi-open", cls="flex gap-2")(
                    Input(
                        name="lead_id",
                        placeholder="lead-YYYYMMDD-xxxxxx",
                        cls="border rounded px-3 py-2",
                    ),
                    Button("Open existing EOI", type="submit", cls=ButtonT.secondary),
                ),
            )
        ),
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
