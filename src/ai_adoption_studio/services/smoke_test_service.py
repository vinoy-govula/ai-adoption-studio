"""SDK smoke test via ai_platform.AIClient."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from ai_adoption_studio.config import settings
from ai_adoption_studio.models.workflow_state import SmokeResult
from ai_adoption_studio.services.wizard_service import WizardService


class SmokeTestService:
    """Run capability-first smoke test against deployed Gateway."""

    def __init__(self, wizard: WizardService | None = None) -> None:
        self._wizard = wizard or WizardService()

    async def run(
        self,
        lead_id: str,
        *,
        capability: str | None = None,
        prompt: str | None = None,
        gateway_url: str | None = None,
        client_factory: Any | None = None,
    ) -> SmokeResult:
        state = self._wizard.get_state(lead_id)
        cap = capability or state.validation.test_capability
        user_prompt = prompt or state.validation.test_prompt
        base_url = gateway_url or settings.gateway_base_url

        if not settings.platform_api_key:
            result = SmokeResult(status="failed", message="Configure STUDIO_PLATFORM_API_KEY")
            self._wizard.update_validation(lead_id, last_smoke_result=result)
            return result

        started = time.perf_counter()
        try:
            if client_factory:
                client = client_factory(api_key=settings.platform_api_key, base_url=base_url)
            else:
                from ai_platform import AIClient

                client = AIClient(api_key=settings.platform_api_key, base_url=base_url)
            client.chat(capability=cap, messages=[{"role": "user", "content": user_prompt}])
            latency_ms = int((time.perf_counter() - started) * 1000)
            result = SmokeResult(
                status="passed",
                latency_ms=latency_ms,
                message="Smoke test passed",
                at=datetime.now(UTC).isoformat(),
            )
        except Exception as exc:
            result = SmokeResult(
                status="failed",
                message=str(exc),
                at=datetime.now(UTC).isoformat(),
            )

        self._wizard.update_validation(lead_id, last_smoke_result=result, test_capability=cap)
        return result


smoke_test_service = SmokeTestService()
