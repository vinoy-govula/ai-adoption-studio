"""Render question-set fields with MonsterUI."""

from __future__ import annotations

from typing import Any

from fasthtml.common import Details, Div, FT, Fieldset, Legend, Li, P, Summary, Ul
from fasthtml.common import *  # noqa: F403
from monsterui.all import LabelCheckboxX, LabelInput, LabelRadio, LabelTextArea
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.services.question_set_loader import Question, QuestionSet

FIELD_HELP: dict[str, str] = {
    "executive_sponsor_identified": (
        "Select this when a named senior sponsor can make prioritisation decisions, remove blockers, "
        "and approve moving from assessment into a customer-facing pilot."
    ),
    "ai_strategy_documented": (
        "Use this to judge whether AI adoption is being driven by a clear business plan or only by ad-hoc interest. "
        "Higher maturity reduces delivery risk."
    ),
    "document_corpus_ready": (
        "Estimate how ready the customer's knowledge base is for a useful assistant. Curated content usually means "
        "fewer discovery and cleanup tasks before the pilot."
    ),
    "data_classification_in_place": (
        "Select this when the customer can identify sensitive, regulated, internal, and public data before ingestion."
    ),
    "compliance_frameworks": (
        "Choose every framework that should influence audit, retention, access control, deployment topology, or reporting."
    ),
    "audit_retention_requirement": (
        "Select the minimum retention period the customer expects for AI request and governance audit records."
    ),
    "it_ops_capacity": (
        "Assess whether the customer can operate the platform after handover. Lower capacity favours simpler profiles "
        "and more managed support."
    ),
    "deployment_target": (
        "Choose the most likely hosting environment for the first production path. This informs network, data residency, "
        "and edge-routing decisions."
    ),
    "concurrent_users": (
        "Enter expected peak simultaneous users, not total named users. This helps size runtime capacity and concurrency limits."
    ),
    "daily_requests": (
        "Estimate steady-state daily AI calls across chat, retrieval, summarisation, validation, and automation workflows."
    ),
    "target_latency_ms": (
        "Use the median response time the customer considers acceptable. Lower targets may require stronger runtime profiles."
    ),
    "change_champion_identified": (
        "Select this when a business-side owner can coordinate training, pilot feedback, and adoption communications."
    ),
    "staff_ai_literacy": (
        "Estimate the likely user readiness for AI-assisted workflows. Lower literacy increases enablement and support needs."
    ),
    "pilot_department": (
        "Name the first team or department that should receive the pilot, such as Finance, HR, Contact Centre, Legal, or Operations."
    ),
}

OPTION_HELP: dict[str, dict[str, str]] = {
    "ai_strategy_documented": {
        "none": "No documented strategy or agreed AI priorities.",
        "informal": "Intent exists in conversations or workshops, but not yet in an approved document.",
        "draft": "A draft plan exists and can guide pilot scope, but may still need approval.",
        "approved": "Leadership has approved AI priorities, ownership, and expected outcomes.",
    },
    "document_corpus_ready": {
        "none": "No target content has been identified.",
        "scattered": "Useful content exists but is spread across systems or owners.",
        "partially_curated": "Some content is organised and suitable for a pilot.",
        "curated": "The corpus is structured, current, and ready for ingestion or retrieval testing.",
    },
    "audit_retention_requirement": {
        "30_days": "Short operational retention for low-risk pilots.",
        "90_days": "Common pilot retention window with enough history for review.",
        "1_year": "Suitable for regulated or procurement-sensitive environments.",
        "unlimited": "Keep audit history indefinitely until customer policy says otherwise.",
        "disabled": "Only use when audit logging is explicitly out of scope for the pilot.",
    },
    "it_ops_capacity": {
        "none": "No internal team can operate or troubleshoot the platform.",
        "limited": "Some technical support exists, but the pilot should stay simple.",
        "moderate": "The customer can operate standard services with guidance.",
        "strong": "A capable platform or infrastructure team can own operations.",
    },
    "deployment_target": {
        "on_prem_vm": "Customer-hosted VM or server environment.",
        "private_cloud": "Private cloud or controlled tenant environment.",
        "public_cloud": "Managed public cloud environment.",
        "hybrid": "Runtime, gateway, identity, or data will span more than one environment.",
        "undecided": "Use when the customer needs architecture consultation before committing.",
    },
    "staff_ai_literacy": {
        "low": "Users are new to AI tools and will need guided enablement.",
        "mixed": "Some teams are confident while others need support.",
        "moderate": "Most users can adopt with normal onboarding.",
        "high": "Users already understand AI limitations, prompting, and review practices.",
    },
}


def _label(value: str) -> str:
    return value.replace("_", " ").title()


def _field_help(question: Question) -> FT:
    help_text = question.help_text or FIELD_HELP.get(question.id, "")
    option_help = {**OPTION_HELP.get(question.id, {}), **question.option_help}
    items = []

    if help_text:
        items.append(P(help_text, cls="text-sm text-slate-700 mb-2"))
    if question.type in {"select", "multi_select"} and question.options:
        items.append(P("Possible values:", cls="text-xs font-semibold text-slate-600 mb-1"))
        items.append(
            Ul(
                *[
                    Li(
                        f"{_label(opt)}: {option_help.get(opt, 'Select when this best matches the customer context.')}"
                    )
                    for opt in question.options
                ],
                cls="list-disc ml-5 text-xs text-slate-600",
            )
        )
    if question.type == "integer":
        bounds = []
        if question.min is not None:
            bounds.append(f"minimum {question.min}")
        if question.max is not None:
            bounds.append(f"maximum {question.max}")
        if bounds:
            items.append(P(f"Accepted range: {', '.join(bounds)}.", cls="text-xs text-slate-600"))

    if not items:
        items.append(P("Use the best information available from the customer discussion.", cls="text-sm text-slate-700"))

    return Details(
        Summary("Help me choose", cls="cursor-pointer text-xs text-blue-700 underline mt-1"),
        Div(*items, cls="mt-2 rounded border bg-slate-50 p-3"),
    )


def _radio_select(question: Question, current: Any) -> FT:
    selected = "" if current is None else str(current)
    return Fieldset(
        Legend(question.label, cls="font-medium mb-2"),
        Div(cls="grid grid-cols-1 md:grid-cols-2 gap-2")(
            *[
                LabelRadio(
                    _label(opt),
                    name=question.id,
                    value=opt,
                    checked=selected == opt,
                    required=question.required,
                )
                for opt in question.options
            ],
        ),
    )


def question_field(question: Question, value: Any = None, errors: list[str] | None = None) -> FT:
    errors = errors or []
    error_html = P("; ".join(errors), cls="text-red-600 text-sm mt-1") if errors else None
    name = question.id
    current = value if value is not None else question.default

    if question.type == "boolean":
        checked = current is True or str(current).lower() in {"true", "1", "yes"}
        field = LabelCheckboxX(
            question.label,
            name=name,
            value="true",
            checked=checked,
        )
    elif question.type == "textarea":
        field = LabelTextArea(question.label, name=name, value=current or "")
    elif question.type == "select":
        field = _radio_select(question, current)
    elif question.type == "multi_select":
        selected = set(current or [])
        boxes = [
            LabelCheckboxX(opt.replace("_", " ").title(), name=name, value=opt, checked=opt in selected)
            for opt in question.options
        ]
        field = Fieldset(Legend(question.label), *boxes)
    elif question.type == "integer":
        field = LabelInput(
            question.label,
            name=name,
            type="number",
            value=str(current) if current is not None else "",
        )
    elif question.type == "email":
        field = LabelInput(question.label, name=name, type="email", value=current or "")
    else:
        field = LabelInput(question.label, name=name, value=current or "")

    return Div(cls="mb-4")(field, _field_help(question), error_html)


def dynamic_form(
    question_set: QuestionSet,
    *,
    values: dict[str, Any] | None = None,
    errors: dict[str, list[str]] | None = None,
    group_by_dimension: bool = True,
) -> FT:
    values = values or {}
    errors = errors or {}
    if not group_by_dimension:
        return Div(*[question_field(q, values.get(q.id), errors.get(q.id)) for q in question_set.questions])

    dimensions: dict[str, list[Question]] = {}
    for question in question_set.questions:
        dimensions.setdefault(question.dimension, []).append(question)

    sections = []
    for dimension, questions in dimensions.items():
        fields = [question_field(q, values.get(q.id), errors.get(q.id)) for q in questions]
        sections.append(Fieldset(Legend(dimension.replace("_", " ").title()), *fields, cls="mb-6"))
    return Div(*sections)
