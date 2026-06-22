"""Certification orchestration service."""

from __future__ import annotations

from typing import Any

from ai_adoption_studio.adapters.cursor_agent import CursorAgentBridge
from ai_adoption_studio.models.certification_verdict import CertificationVerdict
from ai_adoption_studio.services.status_aggregator import StatusAggregator
from ai_adoption_studio.services.validation_ui_service import ValidationUIService
from ai_adoption_studio.services.wizard_service import WizardService


class CertificationService:
    """Coordinate certify flow with context assembly."""

    def __init__(
        self,
        wizard: WizardService | None = None,
        bridge: CursorAgentBridge | None = None,
        status: StatusAggregator | None = None,
        validation: ValidationUIService | None = None,
    ) -> None:
        self._wizard = wizard or WizardService()
        self._bridge = bridge or CursorAgentBridge()
        self._status = status or StatusAggregator()
        self._validation = validation or ValidationUIService()

    async def certify(self, lead_id: str) -> CertificationVerdict:
        manifest = self._wizard._read_manifest(lead_id) or {}
        report = self._validation.load_report(lead_id)
        snapshot = await self._status.poll(lead_id, manifest=manifest)
        return await self._bridge.certify(
            lead_id,
            manifest=manifest,
            deployment_report=report,
            status_snapshot=snapshot.model_dump(),
        )


certification_service = CertificationService()
