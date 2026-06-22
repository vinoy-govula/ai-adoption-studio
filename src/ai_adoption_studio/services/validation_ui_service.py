"""Validation report helpers for wizard UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_adoption_studio.services.store import LeadStore


MANUAL_CHECK_IDS = [
    "cc_runtime_ready",
    "cc_uptime",
    "cc_streams",
    "cc_total_requests",
    "cc_rate_limited",
    "cc_users",
    "cc_api_keys",
    "cc_audit",
    "cc_capabilities",
    "cc_models",
]


class ValidationUIService:
    """Load and update deployment-report for manual checklist."""

    def __init__(self, store: LeadStore | None = None) -> None:
        self._store = store or LeadStore()

    def _report_path(self, lead_id: str) -> Path:
        return self._store._store.lead_dir(lead_id) / "deployment-report.json"

    def load_report(self, lead_id: str) -> dict[str, Any] | None:
        path = self._report_path(lead_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def ensure_manual_checks(self, lead_id: str) -> dict[str, Any]:
        report = self.load_report(lead_id) or {
            "schema_version": "1.0.0",
            "status": "pending",
            "checks": [],
            "manual_control_centre_checks": [],
        }
        existing = {item["id"]: item for item in report.get("manual_control_centre_checks", [])}
        checks = []
        for check_id in MANUAL_CHECK_IDS:
            item = existing.get(check_id, {"id": check_id, "status": "pending", "notes": ""})
            checks.append(item)
        report["manual_control_centre_checks"] = checks
        return report

    def save_manual_checks(self, lead_id: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
        report = self.ensure_manual_checks(lead_id)
        report["manual_control_centre_checks"] = checks
        path = self._report_path(lead_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    def checklist_complete(self, lead_id: str) -> bool:
        report = self.ensure_manual_checks(lead_id)
        manual = report.get("manual_control_centre_checks", [])
        return all(item.get("status") == "complete" for item in manual)


validation_ui_service = ValidationUIService()
