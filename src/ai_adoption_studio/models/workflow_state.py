"""Workflow state models for operator wizard."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class StepStatus(StrEnum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    BLOCKED = "blocked"


STEP_ORDER: list[str] = [
    "eoi_review",
    "qualify",
    "assessment_form",
    "assessment_run",
    "narrative",
    "cp2_approve",
    "branding_kit",
    "deploy_lab",
    "live_status",
    "llm_test_select",
    "validate",
    "manual_cc",
    "cp3_approve",
    "ship_prep",
    "cp4_approve",
    "export",
]

STEP_LABELS: dict[str, str] = {
    "eoi_review": "EOI Review",
    "qualify": "Qualify",
    "assessment_form": "Questionnaire",
    "assessment_run": "Assessment",
    "narrative": "Narrative",
    "cp2_approve": "Client approval",
    "branding_kit": "Playground kit",
    "deploy_lab": "Deploy",
    "live_status": "Live status",
    "llm_test_select": "Test LLM",
    "validate": "Validate",
    "manual_cc": "CC checks",
    "cp3_approve": "Lab sign-off",
    "ship_prep": "Ship prep",
    "cp4_approve": "Handover",
    "export": "Export",
}


class StepRecord(BaseModel):
    status: StepStatus = StepStatus.LOCKED
    completed_at: str | None = None


class SmokeResult(BaseModel):
    status: str = "unknown"
    latency_ms: int | None = None
    message: str = ""
    at: str | None = None


class ValidationState(BaseModel):
    test_capability: str = "chat"
    test_model_override: str | None = None
    test_prompt: str = "Summarize this deployment in one sentence."
    selection_source: str = "recommended"
    last_smoke_result: SmokeResult | None = None


class ActiveJobs(BaseModel):
    deploy: str | None = None
    validate_job: str | None = None
    cursor_certify: str | None = None


class WorkflowState(BaseModel):
    schema_version: str = "1.0.0"
    lead_id: str
    current_step: str = "eoi_review"
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_by: str = "operator"
    steps: dict[str, StepRecord] = Field(default_factory=dict)
    validation: ValidationState = Field(default_factory=ValidationState)
    artifact_versions: dict[str, int] = Field(default_factory=dict)
    active_jobs: ActiveJobs = Field(default_factory=ActiveJobs)
    branding: dict[str, Any] = Field(default_factory=dict)
    draft_payloads: dict[str, dict[str, Any]] = Field(default_factory=dict)
    cp3_checklist_complete: bool = False
    cp3_override_reason: str = ""
    ship_prep_viewed: bool = False

    def step_meta(self) -> list[dict[str, str]]:
        return [
            {
                "id": step_id,
                "label": STEP_LABELS.get(step_id, step_id),
                "status": self.steps.get(step_id, StepRecord()).status.value,
            }
            for step_id in STEP_ORDER
        ]
