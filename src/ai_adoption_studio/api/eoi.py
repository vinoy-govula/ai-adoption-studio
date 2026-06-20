"""Public EOI API."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request
from pydantic import BaseModel, Field

from ai_adoption_studio.config import settings
from ai_adoption_studio.services.store import LeadStore

_rate_buckets: dict[str, list[float]] = defaultdict(list)


class EOIConsent(BaseModel):
    privacy_policy_accepted: bool
    contact_permitted: bool
    marketing_opt_in: bool = False


class EOISubmission(BaseModel):
    source: str = "website"
    consent: EOIConsent
    responses: dict[str, Any] = Field(default_factory=dict)


def _check_rate_limit(client_ip: str) -> None:
    now = time.time()
    window = _rate_buckets[client_ip]
    window[:] = [stamp for stamp in window if now - stamp < 60]
    if len(window) >= settings.eoi_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    window.append(now)


def register_eoi_routes(app) -> None:
    @app.post("/api/v1/eoi")
    async def submit_eoi(payload: EOISubmission, request: Request) -> dict[str, Any]:
        from ai_adoption_studio.services.store import lead_store

        _check_rate_limit(request.client.host if request.client else "unknown")
        if not payload.consent.privacy_policy_accepted or not payload.consent.contact_permitted:
            raise HTTPException(status_code=400, detail="Consent required")
        record = lead_store.create_eoi(payload.model_dump())
        return {"success": True, "data": record}
