"""Aggregate platform health into StatusSnapshot."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from ai_adoption_studio.adapters.control_centre_client import ControlCentreClient
from ai_adoption_studio.adapters.gateway_client import GatewayClient
from ai_adoption_studio.adapters.runtime_manager_client import RuntimeManagerClient
from ai_adoption_studio.services.infrastructure_urls import resolve_urls
from ai_adoption_studio.services.wizard_service import WizardService


class LayerStatus(BaseModel):
    status: str = "unknown"
    summary: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class StatusSnapshot(BaseModel):
    polled_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    overall: str = "unknown"
    infrastructure_stage: str = "developer"
    edge_profile: str = "none"
    layers: dict[str, LayerStatus] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class StatusAggregator:
    """Poll Gateway, RM, CC and merge SDK smoke from workflow state."""

    MANIFEST_FILE = "playground-kit.manifest.json"

    def __init__(self, wizard: WizardService | None = None) -> None:
        self._wizard = wizard or WizardService()
        self._fail_counts: dict[str, int] = {}

    def _load_manifest(self, lead_id: str) -> dict[str, Any] | None:
        path = self._wizard._lead_dir(lead_id) / self.MANIFEST_FILE
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    async def _probe_health(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def poll(self, lead_id: str, *, manifest: dict[str, Any] | None = None) -> StatusSnapshot:
        manifest = manifest or self._load_manifest(lead_id)
        urls = resolve_urls(manifest)
        state = self._wizard.get_state(lead_id)
        errors: list[str] = []
        layers: dict[str, LayerStatus] = {}

        async def _layer(name: str, coro) -> None:
            try:
                result = await coro
                layers[name] = LayerStatus(status="healthy", summary="OK", details=result)
            except Exception as exc:
                errors.append(f"{name}: {exc}")
                layers[name] = LayerStatus(status="unhealthy", summary=str(exc))

        tasks = [
            _layer("runtime", RuntimeManagerClient(base_url=urls.runtime_manager_url).healthz()),
            _layer(
                "gateway",
                GatewayClient(base_url=urls.gateway_base_url).healthz(),
            ),
        ]

        if urls.use_edge_routing:
            tasks.append(_layer("edge", self._probe_health(urls.gateway_health_url)))
            tasks.append(
                _layer(
                    "control_centre",
                    self._probe_health(urls.control_centre_health_url),
                )
            )
        else:
            tasks.append(
                _layer(
                    "control_centre",
                    ControlCentreClient(base_url=urls.control_centre_url).healthz(),
                )
            )

        await asyncio.gather(*tasks)

        smoke = state.validation.last_smoke_result
        if smoke and smoke.status == "passed":
            layers["sdk"] = LayerStatus(
                status="healthy",
                summary=f"Last smoke passed ({smoke.latency_ms}ms)",
                details=smoke.model_dump(),
            )
        else:
            layers["sdk"] = LayerStatus(status="unknown", summary="No smoke run yet")

        unhealthy = [name for name, layer in layers.items() if layer.status == "unhealthy"]
        if "gateway" in unhealthy or "edge" in unhealthy:
            overall = "unhealthy"
        elif unhealthy:
            overall = "degraded"
        elif all(layer.status == "healthy" for layer in layers.values() if layer.status != "unknown"):
            overall = "healthy"
        else:
            overall = "degraded" if errors else "unknown"

        self._fail_counts[lead_id] = 0 if not errors else self._fail_counts.get(lead_id, 0) + 1
        return StatusSnapshot(
            overall=overall,
            infrastructure_stage=urls.infrastructure_stage,
            edge_profile=urls.edge_profile,
            layers=layers,
            errors=errors,
        )


status_aggregator = StatusAggregator()
