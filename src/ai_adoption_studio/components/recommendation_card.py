"""Assessment recommendation display."""

from __future__ import annotations

from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403


def recommendation_card(report: dict[str, Any]) -> FT:
    rec = report.get("recommendation", {})
    readiness = report.get("readiness", {})
    pack = rec.get("recommended_pack", "unknown")
    confidence = rec.get("confidence", 0)
    architect_review = rec.get("architect_review_required", False)

    alerts = []
    if architect_review:
        alerts.append(Alert("Architect review recommended before client presentation.", cls=AlertT.warning))

    rule_trace = rec.get("rule_trace", [])
    trace_rows = []
    for entry in rule_trace[:20]:
        if isinstance(entry, dict):
            trace_rows.append(
                Tr(Td(entry.get("rule_id", "")), Td(entry.get("outcome", "")), Td(str(entry.get("detail", ""))))
            )
        else:
            trace_rows.append(Tr(Td(str(entry)), Td("matched"), Td("")))

    return Div(
        *alerts,
        Card(
            H3("Recommendation", cls="font-semibold mb-2"),
            Div(cls="grid grid-cols-2 gap-4 mb-4")(
                Div(P("Pack", cls="text-sm text-slate-500"), P(str(pack), cls="font-bold text-lg")),
                Div(
                    P("Confidence", cls="text-sm text-slate-500"),
                    P(f"{confidence:.0%}", cls="font-bold text-lg"),
                ),
            ),
            Details(
                Summary("Rule trace"),
                Table(cls="w-full text-sm mt-2")(
                    Thead(Tr(Th("Rule"), Th("Outcome"), Th("Detail"))),
                    Tbody(*trace_rows) if trace_rows else Tbody(Tr(Td("No trace", colspan="3"))),
                ),
            ),
            cls="mb-4",
        ),
        Card(
            H3("Readiness scores", cls="font-semibold mb-2"),
            Ul(*[Li(f"{k}: {v}") for k, v in readiness.items()]),
        ),
    )
