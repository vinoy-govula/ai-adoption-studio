"""Branding form for playground kit."""

from __future__ import annotations

from typing import Any

from fasthtml.common import Details, Div, FT, Form, H4, Li, P, Summary, Ul
from fasthtml.common import *  # noqa: F403
from monsterui.all import Card, LabelCheckboxX, LabelInput, LabelRadio, LabelTextArea
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.components.htmx import operator_hx_headers
from ai_adoption_studio.config import settings


def _help(text: str, *items: str) -> FT:
    return Details(
        Summary("Help me choose", cls="cursor-pointer text-xs text-blue-700 underline mt-1"),
        Div(
            P(text, cls="text-sm text-slate-700 mb-2"),
            Ul(*[Li(item) for item in items], cls="list-disc ml-5 text-xs text-slate-600") if items else "",
            cls="mt-2 rounded border bg-slate-50 p-3",
        ),
        cls="mb-3",
    )


def branding_form(
    lead_id: str,
    values: dict[str, Any] | None = None,
    *,
    model_picker: FT | None = None,
) -> FT:
    auth = operator_hx_headers()
    v = values or {}
    stage = v.get("infrastructure_stage", "playground")
    use_edge = v.get("use_edge_overlay", stage == "playground")
    default_url = v.get("public_url") or (
        "http://localhost:8000"
        if stage == "developer"
        else "http://localhost"
        if use_edge
        else ""
    )

    infrastructure = Card(
        H4("Infrastructure stage", cls="font-semibold mt-2"),
        P(
            "Select how this playground will be accessed. See deployment-catalog "
            "docs/infrastructure-journey.md for stage details.",
            cls="text-sm text-slate-600 mb-2",
        ),
        _help(
            "Choose the infrastructure stage that best matches the customer conversation.",
            "Developer: local-only testing, usually no edge routing.",
            "Playground: customer-facing single URL with optional edge overlay.",
            "Production preview: closer to customer edge integration and handover planning.",
        ),
        Div(cls="flex flex-col gap-2 mb-4")(
            LabelRadio(
                "Developer (localhost, no edge)",
                name="infrastructure_stage",
                value="developer",
                checked=stage == "developer",
            ),
            LabelRadio(
                "Playground (single URL, optional edge overlay)",
                name="infrastructure_stage",
                value="playground",
                checked=stage == "playground",
            ),
            LabelRadio(
                "Production preview (customer edge integration)",
                name="infrastructure_stage",
                value="production_preview",
                checked=stage == "production_preview",
            ),
        ),
        LabelCheckboxX(
            "Use optional edge overlay (Playground stage)",
            name="use_edge_overlay",
            value="true",
            checked=bool(use_edge),
        ),
        _help(
            "Use the overlay when the playground needs one public entry point that routes to Gateway and Control Centre paths.",
            "Select for customer-facing playground demos.",
            "Leave off for localhost/developer-only runs or when customer edge owns routing.",
        ),
        Card(
            P("Path contract:", cls="font-semibold text-sm"),
            Ul(
                Li("/healthz → Gateway"),
                Li("/api/v1/* → Gateway"),
                Li("/control-centre/* → Control Centre"),
            ),
            cls="bg-slate-50 text-sm mb-2 p-3",
        ),
        cls="p-4",
    )

    branding_inputs = Card(
        Div(cls="grid md:grid-cols-2 gap-3")(
            Div(
                LabelInput("Client slug", name="client_slug", value=v.get("client_slug", "")),
                _help("Short lowercase identifier used in generated artifact names and URLs. Example: acme-health."),
            ),
            Div(
                LabelInput("Display name", name="display_name", value=v.get("display_name", "")),
                _help("Customer-facing name shown in generated materials. Example: Acme Health AI Playground."),
            ),
            Div(cls="md:col-span-2")(
                LabelTextArea("Welcome message", name="welcome_message", value=v.get("welcome_message", "")),
                _help("Introductory message for pilot users. Keep it specific to the use case and include any safe-use reminder."),
            ),
            Div(
                LabelInput("Logo URL", name="logo_url", value=v.get("logo_url", "")),
                _help("Optional HTTPS URL for customer branding. Leave blank if no approved logo asset is available."),
            ),
            Div(
                LabelInput(
                    "Public URL",
                    name="public_url",
                    value=default_url or v.get("public_url", settings.gateway_base_url),
                    placeholder="https://playground-client.example.com",
                ),
                _help(
                    "External URL users will open for the playground.",
                    "Developer default: http://localhost:8000.",
                    "Playground with edge overlay: http://localhost (routes Gateway and Control Centre paths).",
                    "Playground or preview: use the customer-approved single URL when available.",
                ),
            ),
            Div(
                LabelInput("TTL (days)", name="ttl_days", value=str(v.get("ttl_days", 30))),
                _help("How long the playground should remain active before review or cleanup. Common values: 7, 14, 30."),
            ),
        ),
        cls="p-4",
    )

    return Form(
        id="step-form-branding_kit",
        hx_post=f"/wizard/{lead_id}/branding_kit",
        hx_target="#step-content",
        hx_swap="innerHTML",
        hx_headers=auth,
    )(
        Div(cls="grid xl:grid-cols-[1.25fr_0.95fr] gap-4 items-start")(
            model_picker or "",
            Div(infrastructure, branding_inputs, cls="space-y-4"),
        ),
    )
