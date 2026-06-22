"""HTTP adapter for Runtime Manager."""

from __future__ import annotations

from typing import Any

import httpx

from ai_adoption_studio.config import settings


class RuntimeManagerClient:
    """Read-only Runtime Manager API client."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        self._base_url = (base_url or settings.runtime_manager_base_url).rstrip("/")
        self._timeout = timeout

    async def healthz(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/healthz")
            response.raise_for_status()
            return response.json()
