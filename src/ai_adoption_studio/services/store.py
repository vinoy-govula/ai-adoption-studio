"""File-backed lead artifact store."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from ai_runtime_manager.assessment.storage import ArtifactStore

from ai_adoption_studio.config import settings


class LeadStore:
    """Persist EOI, assessment, and related artifacts per lead."""

    def __init__(self, root=None) -> None:
        self._store = ArtifactStore(root or settings.data_root)

    def create_eoi(self, payload: dict[str, Any]) -> dict[str, Any]:
        lead_id = payload.get("lead_id") or f"lead-{datetime.now(UTC).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        eoi_id = payload.get("eoi_id") or str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        record = {
            "schema_version": "1.0.0",
            "eoi_id": eoi_id,
            "lead_id": lead_id,
            "submitted_at": payload.get("submitted_at", now),
            "source": payload.get("source", "website"),
            "consent": payload.get("consent", {}),
            "responses": payload.get("responses", {}),
            "pipeline_status": payload.get("pipeline_status", "new_lead"),
        }
        self._store.write_json(lead_id, "eoi-intent.json", record)
        return record

    def get_eoi(self, lead_id: str) -> dict[str, Any]:
        return self._store.read_json(lead_id, "eoi-intent.json")

    def save_internal_responses(self, lead_id: str, internal: dict[str, Any]) -> None:
        self._store.write_json(lead_id, "internal-responses.json", internal)

    def get_internal_responses(self, lead_id: str) -> dict[str, Any] | None:
        path = self._store.lead_dir(lead_id) / "internal-responses.json"
        if not path.exists():
            return None
        return self._store.read_json(lead_id, "internal-responses.json")

    def save_assessment_report(self, lead_id: str, report: dict[str, Any]) -> None:
        self._store.write_json(lead_id, "assessment-report.json", report)

    def get_assessment_report(self, lead_id: str) -> dict[str, Any] | None:
        path = self._store.lead_dir(lead_id) / "assessment-report.json"
        if not path.exists():
            return None
        return self._store.read_json(lead_id, "assessment-report.json")

    def list_leads(self) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        for lead_id in self._store.list_lead_ids():
            eoi = self.get_eoi(lead_id)
            leads.append(
                {
                    "lead_id": lead_id,
                    "org_name": eoi.get("responses", {}).get("org_name", lead_id),
                    "pipeline_status": eoi.get("pipeline_status", "new_lead"),
                    "submitted_at": eoi.get("submitted_at", ""),
                    "industry": eoi.get("responses", {}).get("industry", ""),
                }
            )
        return sorted(leads, key=lambda item: item.get("submitted_at", ""), reverse=True)

    @property
    def artifact_root(self):
        return self._store.root


lead_store = LeadStore()
