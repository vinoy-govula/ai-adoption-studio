from fasthtml.common import *  # noqa: F403

from ai_adoption_studio.layouts.base import page_layout


def leads_page(leads: list[dict], message: str = "") -> FT:
    rows = [
        Tr(
            Td(lead["lead_id"]),
            Td(lead.get("org_name", "")),
            Td(lead.get("industry", "")),
            Td(lead.get("pipeline_status", "")),
            Td(lead.get("submitted_at", "")),
            Td(A("Assess", href=f"/leads/{lead['lead_id']}", cls="text-blue-600 underline")),
        )
        for lead in leads
    ]
    return page_layout(
        "Leads",
        "leads",
        H1("Leads inbox", cls="text-2xl font-bold mb-4"),
        P(message, cls="text-green-700 mb-4") if message else "",
        Table(cls="min-w-full bg-white shadow rounded")(
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
            Tbody(*rows),
        ),
    )


def assessment_page(
    lead_id: str,
    eoi: dict,
    report: dict | None,
    narrative_path: str | None,
    message: str = "",
) -> FT:
    responses = eoi.get("responses", {})
    rec = (report or {}).get("recommendation", {})
    readiness = (report or {}).get("readiness", {})
    return page_layout(
        "Assessment",
        "leads",
        H1(f"Assessment — {responses.get('org_name', lead_id)}", cls="text-2xl font-bold mb-4"),
        P(message, cls="text-green-700 mb-4") if message else "",
        Div(cls="grid grid-cols-2 gap-6")(
            Div(cls="bg-white p-4 rounded shadow")(
                H2("Internal questionnaire", cls="font-semibold mb-3"),
                Form(method="post", action=f"/leads/{lead_id}/assess")(
                    Label("Executive sponsor identified"),
                    Input(type="checkbox", name="executive_sponsor_identified", value="true"),
                    Label("Concurrent users", cls="block mt-2"),
                    Input(type="number", name="concurrent_users", value="25", cls="border p-2"),
                    Label("Daily requests", cls="block mt-2"),
                    Input(type="number", name="daily_requests", value="8000", cls="border p-2"),
                    Label("IT ops capacity", cls="block mt-2"),
                    Select(
                        Option("moderate", value="moderate", selected=True),
                        Option("strong", value="strong"),
                        Option("limited", value="limited"),
                        Option("none", value="none"),
                        name="it_ops_capacity",
                        cls="border p-2",
                    ),
                    Label("Deployment target", cls="block mt-2"),
                    Select(
                        Option("private_cloud", value="private_cloud", selected=True),
                        Option("on_prem_vm", value="on_prem_vm"),
                        Option("hybrid", value="hybrid"),
                        Option("undecided", value="undecided"),
                        name="deployment_target",
                        cls="border p-2",
                    ),
                    Button("Run assessment", type="submit", cls="mt-4 bg-blue-600 text-white px-4 py-2 rounded"),
                ),
            ),
            Div(cls="bg-white p-4 rounded shadow")(
                H2("Recommendation", cls="font-semibold mb-3"),
                P(f"Pack: {rec.get('recommended_pack', 'n/a')}"),
                P(f"Confidence: {rec.get('confidence', 'n/a')}"),
                P(f"Overall readiness: {readiness.get('overall_score', 'n/a')}"),
                P(f"Narrative: {narrative_path or 'not generated'}"),
                Form(method="post", action=f"/leads/{lead_id}/qualify", cls="mt-4")(
                    Button("Qualify lead (cp1)", type="submit", cls="bg-slate-700 text-white px-3 py-1 rounded mr-2"),
                ),
                Form(method="post", action=f"/leads/{lead_id}/approve-cp2", cls="mt-2")(
                    Input(name="actor", placeholder="Approver email", cls="border p-2 mr-2"),
                    Button("Approve cp2", type="submit", cls="bg-green-700 text-white px-3 py-1 rounded"),
                ),
                Form(method="post", action=f"/leads/{lead_id}/narrative", cls="mt-2")(
                    Button("Regenerate narrative", type="submit", cls="bg-indigo-700 text-white px-3 py-1 rounded"),
                ),
            ),
        ),
    )


def export_page(files: list[str], message: str = "") -> FT:
    return page_layout(
        "Export",
        "export",
        H1("Pipeline CSV export", cls="text-2xl font-bold mb-4"),
        P(message, cls="text-green-700 mb-4") if message else "",
        Form(method="post", action="/export")(
            Button("Export pipeline CSV", type="submit", cls="bg-blue-600 text-white px-4 py-2 rounded"),
        ),
        Ul(*[Li(name) for name in files], cls="mt-4 list-disc ml-6"),
    )


def eoi_form_page(message: str = "") -> FT:
    return page_layout(
        "EOI Form",
        "eoi",
        H1("Public EOI questionnaire", cls="text-2xl font-bold mb-4"),
        P(message, cls="text-green-700 mb-4") if message else "",
        Form(method="post", action="/eoi-form", cls="bg-white p-6 rounded shadow max-w-xl")(
            Label("Organisation name"),
            Input(name="org_name", required=True, cls="block border p-2 w-full mb-3"),
            Label("Industry"),
            Input(name="industry", value="healthcare", cls="block border p-2 w-full mb-3"),
            Label("Contact email"),
            Input(name="contact_email", type="email", required=True, cls="block border p-2 w-full mb-3"),
            Label("Contact name"),
            Input(name="contact_name", required=True, cls="block border p-2 w-full mb-3"),
            Label("Intent"),
            Select(
                Option("explore", value="explore"),
                Option("deploy", value="deploy", selected=True),
                name="intent",
                cls="block border p-2 w-full mb-3",
            ),
            Input(type="checkbox", name="privacy_policy_accepted", value="true", checked=True),
            Label("Privacy policy accepted", cls="ml-2"),
            Input(type="checkbox", name="contact_permitted", value="true", checked=True),
            Label("Contact permitted", cls="ml-2 block mb-3"),
            Button("Submit EOI", type="submit", cls="bg-blue-600 text-white px-4 py-2 rounded"),
        ),
    )
