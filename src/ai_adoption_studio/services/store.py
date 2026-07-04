"""File-backed lead artifact store."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from ai_runtime_manager.assessment.storage import ArtifactStore

from ai_adoption_studio.config import settings


class LeadStore:
    """Persist EOI, assessment, and related artifacts per lead."""

    EOI_FILE = "eoi-intent.json"

    def __init__(self, root=None) -> None:
        self._store = ArtifactStore(root or settings.data_root)

    def _eoi_path(self, lead_id: str):
        return self._store.root / lead_id / self.EOI_FILE

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
        self._store.write_json(lead_id, self.EOI_FILE, record)
        return record

    def update_eoi(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_eoi(lead_id)
        now = datetime.now(UTC).isoformat()
        record = {
            "schema_version": existing.get("schema_version", "1.0.0"),
            "eoi_id": existing.get("eoi_id") or payload.get("eoi_id") or str(uuid.uuid4()),
            "lead_id": lead_id,
            "submitted_at": existing.get("submitted_at", now),
            "updated_at": now,
            "source": payload.get("source", existing.get("source", "website")),
            "consent": payload.get("consent", existing.get("consent", {})),
            "responses": payload.get("responses", existing.get("responses", {})),
            "pipeline_status": payload.get("pipeline_status", existing.get("pipeline_status", "new_lead")),
        }
        self._store.write_json(lead_id, self.EOI_FILE, record)
        return record

    def get_eoi(self, lead_id: str) -> dict[str, Any]:
        return json.loads(self._eoi_path(lead_id).read_text(encoding="utf-8"))

    def eoi_exists(self, lead_id: str) -> bool:
        return self._eoi_path(lead_id).exists()

    def cleanup_incomplete_leads(self) -> list[str]:
        """Archive lead folders that cannot be opened as EOIs."""
        cleaned: list[str] = []
        archive_root = self._store.root / ".incomplete-leads"
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        for lead_id in self._store.list_lead_ids():
            if not lead_id.startswith("lead-"):
                continue
            try:
                self.get_eoi(lead_id)
                continue
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            lead_dir = self._store.root / lead_id
            if not lead_dir.exists():
                continue
            archive_root.mkdir(parents=True, exist_ok=True)
            target = archive_root / lead_id
            if target.exists():
                target = archive_root / f"{lead_id}-{timestamp}"
            lead_dir.rename(target)
            cleaned.append(lead_id)
        return cleaned

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
            try:
                eoi = self.get_eoi(lead_id)
            except (FileNotFoundError, json.JSONDecodeError):
                continue
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
