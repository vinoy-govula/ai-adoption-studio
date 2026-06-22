"""Dynamic form validation tests."""

from __future__ import annotations

from ai_adoption_studio.services.form_validator import FormValidator
from ai_adoption_studio.services.question_set_loader import Question, QuestionSet


def _sample_set() -> QuestionSet:
    return QuestionSet(
        schema_version="1.0.0",
        question_set_id="test",
        questions=[
            Question(id="name", type="text", label="Name", required=True),
            Question(id="email", type="email", label="Email", required=True),
            Question(id="count", type="integer", label="Count", required=True, min=1, max=10),
            Question(id="tier", type="select", label="Tier", required=True, options=["a", "b"]),
            Question(id="tags", type="multi_select", label="Tags", required=True, options=["x", "y"]),
            Question(id="active", type="boolean", label="Active", required=False),
        ],
    )


def test_required_fields() -> None:
    validator = FormValidator()
    errors = validator.validate(_sample_set(), {})
    assert "name" in errors
    assert "email" in errors


def test_email_validation() -> None:
    validator = FormValidator()
    errors = validator.validate(_sample_set(), {"name": "A", "email": "bad", "count": 2, "tier": "a", "tags": ["x"]})
    assert "email" in errors


def test_integer_bounds() -> None:
    validator = FormValidator()
    errors = validator.validate(
        _sample_set(),
        {"name": "A", "email": "a@b.com", "count": 99, "tier": "a", "tags": ["x"]},
    )
    assert "count" in errors


def test_select_and_multi_select() -> None:
    validator = FormValidator()
    errors = validator.validate(
        _sample_set(),
        {"name": "A", "email": "a@b.com", "count": 2, "tier": "invalid", "tags": ["z"]},
    )
    assert "tier" in errors
    assert "tags" in errors


def test_coerce_boolean_and_integer() -> None:
    validator = FormValidator()
    data = validator.coerce(
        _sample_set(),
        {"name": "A", "email": "a@b.com", "count": "3", "tier": "a", "tags": "x", "active": "true"},
    )
    assert data["count"] == 3
    assert data["active"] is True
    assert data["tags"] == ["x"]
