"""Load and cache JSON question sets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ai_adoption_studio.config import settings


class Question(BaseModel):
    id: str
    type: str
    label: str
    required: bool = False
    visibility: str = "internal"
    dimension: str = "general"
    options: list[str] = Field(default_factory=list)
    min: int | None = None
    max: int | None = None
    max_length: int | None = None
    default: Any = None


class QuestionSet(BaseModel):
    schema_version: str
    question_set_id: str
    visibility: str = "internal"
    description: str = ""
    extends: str | None = None
    questions: list[Question] = Field(default_factory=list)


class QuestionSetLoader:
    """Load question sets from JSON files with simple mtime cache."""

    def __init__(self) -> None:
        self._cache: dict[str, QuestionSet] = {}
        self._mtimes: dict[str, float] = {}

    def load(self, path: Path) -> QuestionSet:
        key = str(path.resolve())
        mtime = path.stat().st_mtime if path.exists() else 0.0
        if key in self._cache and self._mtimes.get(key) == mtime:
            return self._cache[key]
        data = json.loads(path.read_text(encoding="utf-8"))
        qs = QuestionSet.model_validate(data)
        self._cache[key] = qs
        self._mtimes[key] = mtime
        return qs

    def get_eoi(self) -> QuestionSet:
        return self.load(settings.eoi_question_set_path)

    def get_internal(self) -> QuestionSet:
        return self.load(settings.internal_question_set_path)

    def get_by_id(self, set_id: str) -> QuestionSet:
        if set_id in {"eoi-public-v1", "eoi"}:
            return self.get_eoi()
        return self.get_internal()


question_set_loader = QuestionSetLoader()
