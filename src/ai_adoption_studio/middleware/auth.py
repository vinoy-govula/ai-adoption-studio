"""Operator route authentication."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ai_adoption_studio.config import settings

PROTECTED_PREFIXES = ("/wizard", "/api/leads", "/api/jobs", "/api/cursor")


def _extract_api_key(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.headers.get("x-studio-api-key") or request.cookies.get("studio_api_key")


def _is_protected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


class InternalAuthMiddleware(BaseHTTPMiddleware):
    """Require STUDIO_INTERNAL_API_KEY on operator routes."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not _is_protected(request.url.path):
            return await call_next(request)

        provided = _extract_api_key(request)
        if provided != settings.internal_api_key:
            accept = request.headers.get("accept", "")
            if "text/html" in accept or request.headers.get("hx-request"):
                return Response(
                    content="Unauthorized — set Authorization: Bearer {STUDIO_INTERNAL_API_KEY}",
                    status_code=401,
                    media_type="text/plain",
                )
            return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=401)
        return await call_next(request)
