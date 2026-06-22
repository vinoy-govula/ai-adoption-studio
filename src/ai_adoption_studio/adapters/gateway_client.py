"""HTTP adapter for AI Gateway."""

from __future__ import annotations

from typing import Any

import httpx

from ai_adoption_studio.config import settings


class GatewayClient:
    """Read-only Gateway API client."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._base_url = (base_url or settings.gateway_base_url).rstrip("/")
        self._api_key = api_key or settings.platform_api_key
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def healthz(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/healthz")
            response.raise_for_status()
            return response.json()

    async def list_capabilities(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/api/v1/capabilities",
                headers=self._headers(),
            )
            if response.status_code == 401:
                raise PermissionError("Gateway capabilities API unauthorized")
            response.raise_for_status()
            body = response.json()
            if isinstance(body, dict) and "data" in body:
                return body["data"]
            if isinstance(body, list):
                return body
            return []
