"""Cursor agent bridge (mock-friendly for tests)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, AsyncIterator

from ai_adoption_studio.config import settings
from ai_adoption_studio.models.certification_verdict import CertificationVerdict, EvidenceItem
from ai_adoption_studio.services.redaction import redact_text
from ai_adoption_studio.services.store import LeadStore


class CursorAgentBridge:
    """Certify, troubleshoot, and PIR via Cursor SDK or heuristic fallback."""

    def __init__(self, store: LeadStore | None = None) -> None:
        self._store = store or LeadStore()

    def _runs_dir(self, lead_id: str) -> Path:
        path = self._store._store.lead_dir(lead_id) / "cursor-runs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def certify(
        self,
        lead_id: str,
        *,
        manifest: dict[str, Any],
        deployment_report: dict[str, Any] | None,
        status_snapshot: dict[str, Any],
    ) -> CertificationVerdict:
        run_id = str(uuid.uuid4())
        report_status = (deployment_report or {}).get("status", "unknown")
        overall = status_snapshot.get("overall", "unknown")
        if report_status == "passed" and overall in {"healthy", "degraded"}:
            verdict = CertificationVerdict(
                verdict="pass",
                confidence=0.9,
                evidence=[EvidenceItem(source="deployment-report", finding="Automated validation passed")],
            )
        elif report_status == "failed":
            verdict = CertificationVerdict(
                verdict="fail",
                confidence=0.85,
                evidence=[EvidenceItem(source="deployment-report", finding="Validation failed")],
                recommended_actions=["Review failed checks and re-run validation"],
            )
        else:
            verdict = CertificationVerdict(
                verdict="conditional",
                confidence=0.6,
                conditions=["Complete validation and manual CC checklist"],
            )

        path = self._runs_dir(lead_id) / f"{run_id}-verdict.json"
        path.write_text(json.dumps(verdict.model_dump(), indent=2), encoding="utf-8")
        meta = {
            "run_id": run_id,
            "mode": "certify",
            "lead_id": lead_id,
            "created_at": datetime.now(UTC).isoformat(),
            "workspace": str(settings.cursor_workspace_root),
        }
        (self._runs_dir(lead_id) / f"{run_id}-meta.json").write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )
        return verdict

    async def troubleshoot(
        self,
        lead_id: str,
        *,
        context: dict[str, Any],
        message: str,
        run_id: str | None = None,
    ) -> AsyncIterator[str]:
        safe_log = redact_text(context.get("log_excerpt", ""))
        yield f"Analyzing issue for lead {lead_id}...\n"
        yield f"Context: {context.get('failed_check', 'unknown')}\n"
        yield f"Log excerpt:\n{safe_log}\n"
        yield f"Suggestion: verify Gateway health and STUDIO_PLATFORM_API_KEY.\n"
        yield f"Operator question: {message}\n"

    async def suggest_pir(self, lead_id: str, *, context: dict[str, Any]) -> str:
        return (
            f"# Platform Improvement Record\n\n"
            f"Lead: {lead_id}\n\n"
            f"Finding: {context.get('finding', 'UX or validation friction')}\n\n"
            f"Recommended target: ai-runtime-manager\n"
        )

    def list_runs(self, lead_id: str) -> list[dict[str, Any]]:
        runs = []
        for path in sorted(self._runs_dir(lead_id).glob("*-meta.json"), reverse=True):
            runs.append(json.loads(path.read_text(encoding="utf-8")))
        return runs


cursor_agent_bridge = CursorAgentBridge()
