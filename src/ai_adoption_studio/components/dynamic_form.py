"""Render question-set fields with MonsterUI."""

from __future__ import annotations

from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.services.question_set_loader import Question, QuestionSet


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
        options = [(opt, opt.replace("_", " ").title()) for opt in question.options]
        field = LabelSelect(question.label, *options, name=name, selected=current or "")
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

    return Div(cls="mb-4")(field, error_html)


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
