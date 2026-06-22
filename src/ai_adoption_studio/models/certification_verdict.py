"""Cursor certification verdict schema."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source: str
    finding: str


class CertificationVerdict(BaseModel):
    schema_version: str = "1.0.0"
    verdict: str = "conditional"
    confidence: float = 0.5
    evidence: list[EvidenceItem] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
