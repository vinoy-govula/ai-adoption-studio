"""Validate dynamic form submissions against question sets."""

from __future__ import annotations

import re
from typing import Any

from ai_adoption_studio.services.question_set_loader import Question, QuestionSet

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class FormValidator:
    """Return field-level errors for question set submissions."""

    def validate(self, question_set: QuestionSet, data: dict[str, Any]) -> dict[str, list[str]]:
        errors: dict[str, list[str]] = {}
        for question in question_set.questions:
            field_errors = self._validate_question(question, data.get(question.id))
            if field_errors:
                errors[question.id] = field_errors
        return errors

    def coerce(self, question_set: QuestionSet, raw: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for question in question_set.questions:
            value = raw.get(question.id)
            if value is None or value == "":
                if question.default is not None:
                    result[question.id] = question.default
                continue
            result[question.id] = self._coerce_value(question, value)
        return result

    def _coerce_value(self, question: Question, value: Any) -> Any:
        if question.type == "boolean":
            if isinstance(value, bool):
                return value
            return str(value).lower() in {"true", "1", "yes", "on"}
        if question.type == "integer":
            return int(value)
        if question.type == "multi_select":
            if isinstance(value, list):
                return value
            return [value] if value else []
        return value

    def _validate_question(self, question: Question, value: Any) -> list[str]:
        errors: list[str] = []
        if question.required and self._is_empty(question, value):
            errors.append("This field is required.")
            return errors

        if self._is_empty(question, value):
            return errors

        if question.type == "email" and isinstance(value, str) and not _EMAIL_RE.match(value):
            errors.append("Invalid email address.")

        if question.type == "integer":
            try:
                num = int(value)
            except (TypeError, ValueError):
                errors.append("Must be an integer.")
                return errors
            if question.min is not None and num < question.min:
                errors.append(f"Must be at least {question.min}.")
            if question.max is not None and num > question.max:
                errors.append(f"Must be at most {question.max}.")

        if question.type in {"select", "multi_select"} and question.options:
            if question.type == "select" and value not in question.options:
                errors.append("Invalid selection.")
            if question.type == "multi_select":
                selected = value if isinstance(value, list) else [value]
                invalid = [item for item in selected if item not in question.options]
                if invalid:
                    errors.append("Invalid selection.")

        if question.max_length and isinstance(value, str) and len(value) > question.max_length:
            errors.append(f"Maximum length is {question.max_length}.")

        return errors

    def _is_empty(self, question: Question, value: Any) -> bool:
        if value is None:
            return True
        if question.type == "multi_select":
            return not value or (isinstance(value, list) and len(value) == 0)
        if question.type == "boolean":
            return False
        if isinstance(value, str):
            return value.strip() == ""
        return False


form_validator = FormValidator()
