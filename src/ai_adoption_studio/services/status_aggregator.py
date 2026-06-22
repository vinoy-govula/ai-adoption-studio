"""Aggregate platform health into StatusSnapshot."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from ai_adoption_studio.adapters.control_centre_client import ControlCentreClient
from ai_adoption_studio.adapters.gateway_client import GatewayClient
from ai_adoption_studio.adapters.runtime_manager_client import RuntimeManagerClient
from ai_adoption_studio.services.wizard_service import WizardService


class LayerStatus(BaseModel):
    status: str = "unknown"
    summary: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class StatusSnapshot(BaseModel):
    polled_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    overall: str = "unknown"
    layers: dict[str, LayerStatus] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class StatusAggregator:
    """Poll Gateway, RM, CC and merge SDK smoke from workflow state."""

    def __init__(self, wizard: WizardService | None = None) -> None:
        self._wizard = wizard or WizardService()
        self._fail_counts: dict[str, int] = {}

    async def poll(self, lead_id: str, *, manifest: dict[str, Any] | None = None) -> StatusSnapshot:
        gw = GatewayClient()
        rm = RuntimeManagerClient()
        cc = ControlCentreClient()
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

        await asyncio.gather(
            _layer("runtime", rm.healthz()),
            _layer("gateway", gw.healthz()),
            _layer("control_centre", cc.healthz()),
        )

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
        if "gateway" in unhealthy:
            overall = "unhealthy"
        elif unhealthy:
            overall = "degraded"
        elif all(layer.status == "healthy" for layer in layers.values() if layer.status != "unknown"):
            overall = "healthy"
        else:
            overall = "degraded" if errors else "unknown"

        self._fail_counts[lead_id] = 0 if not errors else self._fail_counts.get(lead_id, 0) + 1
        return StatusSnapshot(overall=overall, layers=layers, errors=errors)


status_aggregator = StatusAggregator()
