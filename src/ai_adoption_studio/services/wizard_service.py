"""Wizard workflow state persistence and step navigation."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_runtime_manager.assessment.checkpoints import checkpoint_status

from ai_adoption_studio.config import settings
from ai_adoption_studio.models.workflow_state import (
    STEP_ORDER,
    StepRecord,
    StepStatus,
    ValidationState,
    WorkflowState,
)
from ai_adoption_studio.services.store import LeadStore

_locks: dict[str, threading.RLock] = {}
_lock_guard = threading.Lock()


def _lead_lock(lead_id: str) -> threading.RLock:
    with _lock_guard:
        if lead_id not in _locks:
            _locks[lead_id] = threading.RLock()
        return _locks[lead_id]


class WizardService:
    """Manage workflow-state.json per lead."""

    WORKFLOW_FILE = "workflow-state.json"
    MANIFEST_FILE = "playground-kit.manifest.json"
    REPORT_FILE = "assessment-report.json"
    INTERNAL_FILE = "internal-responses.json"
    DEPLOYMENT_REPORT = "deployment-report.json"

    def __init__(self, store: LeadStore | None = None) -> None:
        self._store = store or LeadStore()

    def _lead_dir(self, lead_id: str) -> Path:
        return self._store._store.lead_dir(lead_id)

    def _state_path(self, lead_id: str) -> Path:
        return self._lead_dir(lead_id) / self.WORKFLOW_FILE

    def _artifact_exists(self, lead_id: str, name: str) -> bool:
        return (self._lead_dir(lead_id) / name).exists()

    def _read_manifest(self, lead_id: str) -> dict[str, Any] | None:
        path = self._lead_dir(lead_id) / self.MANIFEST_FILE
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _cp2_approved(self, lead_id: str) -> bool:
        report = self._store.get_assessment_report(lead_id)
        if not report:
            return False
        return checkpoint_status(report, "cp2_assessment_approved") == "approved"

    def _cp3_approved(self, lead_id: str) -> bool:
        report = self._store.get_assessment_report(lead_id)
        if not report:
            return False
        return checkpoint_status(report, "cp3_deploy_test_approved") == "approved"

    def _cp4_approved(self, lead_id: str) -> bool:
        report = self._store.get_assessment_report(lead_id)
        if not report:
            return False
        return checkpoint_status(report, "cp4_ship_approved") == "approved"

    def _manifest_active(self, lead_id: str) -> bool:
        manifest = self._read_manifest(lead_id)
        if not manifest:
            return False
        return manifest.get("status") in {"active", "deploying", "validating", "passed"}

    def _validation_passed(self, lead_id: str) -> bool:
        path = self._lead_dir(lead_id) / self.DEPLOYMENT_REPORT
        if not path.exists():
            return False
        report = json.loads(path.read_text(encoding="utf-8"))
        return report.get("status") == "passed"

    def _default_capability(self, lead_id: str) -> str:
        eoi = self._store.get_eoi(lead_id)
        interests = eoi.get("responses", {}).get("use_case_interest", [])
        if "document_summarisation" in interests:
            return "summarization"
        if "sql_analytics" in interests:
            return "sql-analysis"
        return "chat"

    def _compute_step_status(self, lead_id: str, step_id: str, state: WorkflowState) -> StepStatus:
        record = state.steps.get(step_id)
        if record and record.status == StepStatus.COMPLETE:
            return StepStatus.COMPLETE
        if record and record.status == StepStatus.BLOCKED:
            return StepStatus.BLOCKED

        eoi = None
        try:
            eoi = self._store.get_eoi(lead_id)
        except FileNotFoundError:
            pass

        rules: dict[str, bool] = {
            "eoi_review": self._artifact_exists(lead_id, "eoi-intent.json"),
            "qualify": self._step_complete(state, "eoi_review"),
            "assessment_form": (
                self._step_complete(state, "qualify")
                or (eoi is not None and eoi.get("pipeline_status") == "qualified")
            ),
            "assessment_run": self._artifact_exists(lead_id, self.INTERNAL_FILE),
            "narrative": self._artifact_exists(lead_id, self.REPORT_FILE),
            "cp2_approve": self._artifact_exists(lead_id, self.REPORT_FILE),
            "branding_kit": self._cp2_approved(lead_id),
            "deploy_lab": self._artifact_exists(lead_id, self.MANIFEST_FILE) and self._cp2_approved(
                lead_id
            ),
            "live_status": self._manifest_active(lead_id),
            "llm_test_select": self._manifest_active(lead_id),
            "validate": bool(state.validation.test_capability) and self._manifest_active(lead_id),
            "manual_cc": self._artifact_exists(lead_id, self.DEPLOYMENT_REPORT),
            "cp3_approve": self._validation_passed(lead_id) and state.cp3_checklist_complete,
            "ship_prep": self._cp3_approved(lead_id),
            "cp4_approve": state.ship_prep_viewed and self._cp3_approved(lead_id),
            "export": self._cp4_approved(lead_id),
        }

        if not rules.get(step_id, False):
            return StepStatus.LOCKED
        if state.current_step == step_id:
            return StepStatus.IN_PROGRESS
        return StepStatus.AVAILABLE

    def _step_complete(self, state: WorkflowState, step_id: str) -> bool:
        record = state.steps.get(step_id)
        return record is not None and record.status == StepStatus.COMPLETE

    def _refresh_steps(self, lead_id: str, state: WorkflowState) -> WorkflowState:
        for step_id in STEP_ORDER:
            existing = state.steps.get(step_id)
            if existing and existing.status == StepStatus.LOCKED:
                continue
            computed = self._compute_step_status(lead_id, step_id, state)
            if existing and existing.status == StepStatus.COMPLETE:
                continue
            state.steps[step_id] = StepRecord(status=computed)
        return state

    def ensure_state(self, lead_id: str, *, actor: str = "operator") -> WorkflowState:
        path = self._state_path(lead_id)
        with _lead_lock(lead_id):
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                state = WorkflowState.model_validate(data)
            else:
                state = WorkflowState(
                    lead_id=lead_id,
                    current_step="eoi_review",
                    updated_by=actor,
                    validation=ValidationState(
                        test_capability=self._default_capability(lead_id),
                    ),
                )
            state = self._refresh_steps(lead_id, state)
            if state.current_step not in STEP_ORDER:
                state.current_step = "eoi_review"
            self._write_state(lead_id, state)
            return state

    def get_state(self, lead_id: str) -> WorkflowState:
        return self.ensure_state(lead_id)

    def _write_state(self, lead_id: str, state: WorkflowState) -> None:
        state.updated_at = datetime.now(UTC).isoformat()
        path = self._state_path(lead_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def advance(
        self,
        lead_id: str,
        step_id: str,
        *,
        actor: str = "operator",
        mark_complete: bool = True,
    ) -> WorkflowState:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id, actor=actor)
            if step_id not in STEP_ORDER:
                raise ValueError(f"Unknown step: {step_id}")
            status = self._compute_step_status(lead_id, step_id, state)
            if status == StepStatus.LOCKED:
                raise ValueError(f"Step {step_id} is locked")

            if mark_complete:
                state.steps[step_id] = StepRecord(
                    status=StepStatus.COMPLETE,
                    completed_at=datetime.now(UTC).isoformat(),
                )

            idx = STEP_ORDER.index(step_id)
            if idx + 1 < len(STEP_ORDER):
                state.current_step = STEP_ORDER[idx + 1]
            else:
                state.current_step = step_id

            state.updated_by = actor
            state = self._refresh_steps(lead_id, state)
            next_step = state.current_step
            if next_step in state.steps:
                state.steps[next_step] = StepRecord(status=StepStatus.IN_PROGRESS)
            self._write_state(lead_id, state)
            return state

    def go_back(self, lead_id: str, step_id: str | None = None) -> WorkflowState:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id)
            current = step_id or state.current_step
            if current not in STEP_ORDER:
                current = "eoi_review"
            idx = STEP_ORDER.index(current)
            if idx > 0:
                state.current_step = STEP_ORDER[idx - 1]
            state = self._refresh_steps(lead_id, state)
            prev = state.current_step
            state.steps[prev] = StepRecord(status=StepStatus.IN_PROGRESS)
            self._write_state(lead_id, state)
            return state

    def goto_step(self, lead_id: str, step_id: str) -> WorkflowState:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id)
            status = self._compute_step_status(lead_id, step_id, state)
            if status not in {StepStatus.COMPLETE, StepStatus.AVAILABLE, StepStatus.IN_PROGRESS}:
                raise ValueError(f"Cannot navigate to locked step: {step_id}")
            state.current_step = step_id
            state.steps[step_id] = StepRecord(status=StepStatus.IN_PROGRESS)
            state = self._refresh_steps(lead_id, state)
            self._write_state(lead_id, state)
            return state

    def save_draft(
        self,
        lead_id: str,
        step_id: str,
        payload: dict[str, Any],
        *,
        actor: str = "operator",
    ) -> WorkflowState:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id, actor=actor)
            state.draft_payloads[step_id] = payload
            state.updated_by = actor
            self._write_state(lead_id, state)
            return state

    def invalidate_downstream(self, lead_id: str, from_step: str) -> None:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id)
            if from_step not in STEP_ORDER:
                return
        start_idx = STEP_ORDER.index(from_step)
        for i, step_id in enumerate(STEP_ORDER[start_idx:]):
            if i == 0:
                state.steps[step_id] = StepRecord(status=StepStatus.IN_PROGRESS)
            else:
                state.steps[step_id] = StepRecord(status=StepStatus.LOCKED)
            manifest = self._read_manifest(lead_id)
            if manifest and from_step in {"assessment_form", "assessment_run", "narrative"}:
                manifest["status"] = "draft"
                path = self._lead_dir(lead_id) / self.MANIFEST_FILE
                path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            state = self._refresh_steps(lead_id, state)
            self._write_state(lead_id, state)

    def update_validation(self, lead_id: str, **fields: Any) -> WorkflowState:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id)
            data = state.validation.model_dump()
            data.update(fields)
            state.validation = ValidationState.model_validate(data)
            state = self._refresh_steps(lead_id, state)
            self._write_state(lead_id, state)
            return state

    def set_active_job(self, lead_id: str, job_type: str, job_id: str | None) -> WorkflowState:
        field_map = {"deploy": "deploy", "validate": "validate_job", "cursor_certify": "cursor_certify"}
        field = field_map.get(job_type, job_type)
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id)
            setattr(state.active_jobs, field, job_id)
            self._write_state(lead_id, state)
            return state

    def save_branding(self, lead_id: str, branding: dict[str, Any]) -> WorkflowState:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id)
            state.branding = branding
            self._write_state(lead_id, state)
            return state

    def mark_ship_prep_viewed(self, lead_id: str) -> WorkflowState:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id)
            state.ship_prep_viewed = True
            state = self._refresh_steps(lead_id, state)
            self._write_state(lead_id, state)
            return state

    def set_checklist_complete(self, lead_id: str, complete: bool = True) -> WorkflowState:
        with _lead_lock(lead_id):
            state = self.ensure_state(lead_id)
            state.cp3_checklist_complete = complete
            state = self._refresh_steps(lead_id, state)
            self._write_state(lead_id, state)
            return state


wizard_service = WizardService()
