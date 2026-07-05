"""HTTP adapter for Runtime Manager."""

from __future__ import annotations

from typing import Any

import httpx

from ai_adoption_studio.config import settings


class RuntimeManagerClient:
    """Read-only Runtime Manager API client."""

    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        self._base_url = (base_url or settings.runtime_manager_base_url).rstrip("/")
        self._timeout = timeout

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}{path}", params=params)
            response.raise_for_status()
            body = response.json()
            if isinstance(body, dict) and "data" in body:
                return body["data"]
            return body

    async def healthz(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/healthz")
            response.raise_for_status()
            return response.json()

    async def list_presets(self, *, status: str = "certified") -> list[dict[str, Any]]:
        data = await self._get("/api/v1/presets", {"status": status})
        return data if isinstance(data, list) else []

    async def list_models(
        self,
        *,
        status: str = "certified",
        profile: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"status": status}
        if profile:
            params["profile"] = profile
        data = await self._get("/api/v1/models", params)
        return data if isinstance(data, list) else []

    async def get_recommendations(
        self,
        profile: str,
        *,
        has_gpu: bool = True,
        vram_gb: float | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"profile": profile, "has_gpu": has_gpu}
        if vram_gb is not None:
            params["vram_gb"] = vram_gb
        data = await self._get("/api/v1/catalog/recommendations", params)
        return data if isinstance(data, dict) else {}

    async def get_preset_card(self, key: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/presets/{key}/card")

    async def get_model_card(self, key: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/models/{key}/card")
