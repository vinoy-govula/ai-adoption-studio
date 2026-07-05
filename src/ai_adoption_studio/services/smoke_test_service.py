"""Gateway smoke test using OpenAI-compatible chat completions."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from ai_adoption_studio.config import settings
from ai_adoption_studio.models.workflow_state import SmokeResult
from ai_adoption_studio.services.infrastructure_urls import resolve_urls
from ai_adoption_studio.services.platform_credentials_service import platform_credentials_service
from ai_adoption_studio.services.wizard_service import WizardService


def _assistant_content(body: dict[str, Any]) -> str | None:
    if "data" in body and isinstance(body["data"], dict):
        body = body["data"]
    choices = body.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
    return None


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
        manifest_path = self._wizard._lead_dir(lead_id) / WizardService.MANIFEST_FILE
        if manifest_path.exists() and gateway_url is None:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            base_url = resolve_urls(manifest).gateway_base_url

        api_key = platform_credentials_service.resolve_operator_api_key(lead_id)
        provision_error: str | None = None
        if not api_key:
            manifest_path = self._wizard._lead_dir(lead_id) / WizardService.MANIFEST_FILE
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("status") == "active":
                    try:
                        creds = await platform_credentials_service.provision(lead_id)
                        api_key = creds.operator.api_key
                    except Exception as exc:
                        provision_error = str(exc)
        if not api_key:
            message = (
                f"Could not provision lab credentials: {provision_error}"
                if provision_error
                else "No operator API key yet. Complete Deploy to provision lab credentials."
            )
            result = SmokeResult(status="failed", message=message)
            self._wizard.update_validation(lead_id, last_smoke_result=result)
            return result

        started = time.perf_counter()
        try:
            if client_factory:
                client = client_factory(api_key=api_key, base_url=base_url)
                client.chat(capability=cap, messages=[{"role": "user", "content": user_prompt}])
            else:
                async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=60.0) as client:
                    response = await client.post(
                        "/api/v1/chat/completions",
                        json={
                            "capability": cap,
                            "messages": [{"role": "user", "content": user_prompt}],
                        },
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                    response.raise_for_status()
                    body = response.json()
                    if _assistant_content(body) is None:
                        raise ValueError("Gateway returned no assistant content")
            latency_ms = int((time.perf_counter() - started) * 1000)
            result = SmokeResult(
                status="passed",
                latency_ms=latency_ms,
                message="Smoke test passed",
                at=datetime.now(UTC).isoformat(),
            )
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:200]
            if exc.response.status_code == 403 and "Unknown capability" in detail:
                message = (
                    f"Unknown capability '{cap}'. Choose a capability from the Gateway list "
                    "(for example summarization or knowledge-chat)."
                )
            elif exc.response.status_code == 401:
                message = (
                    "Gateway rejected the operator API key. Re-run Deploy to reprovision credentials, "
                    "or set STUDIO_GATEWAY_ADMIN_KEY to the bootstrap admin key."
                )
            else:
                message = f"Gateway returned HTTP {exc.response.status_code}: {detail}"
            result = SmokeResult(status="failed", message=message, at=datetime.now(UTC).isoformat())
        except Exception as exc:
            result = SmokeResult(
                status="failed",
                message=str(exc),
                at=datetime.now(UTC).isoformat(),
            )

        self._wizard.update_validation(lead_id, last_smoke_result=result, test_capability=cap)
        return result


smoke_test_service = SmokeTestService()
