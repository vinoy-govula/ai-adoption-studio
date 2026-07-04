"""Operator route authentication."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ai_adoption_studio.config import settings

PROTECTED_PREFIXES = ("/wizard", "/api/leads", "/api/jobs", "/api/cursor")
AUTH_COOKIE_NAME = "studio_api_key"


def _extract_api_key(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    # SSE/EventSource cannot set headers; accept the internal key via cookie or
    # query param ("k") for same-origin streaming. Internal tool, static key.
    return (
        request.headers.get("x-studio-api-key")
        or request.cookies.get(AUTH_COOKIE_NAME)
        or request.query_params.get("k")
    )


def _is_protected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def _accepts_html(request: Request) -> bool:
    return "text/html" in request.headers.get("accept", "")


def _set_browser_auth_cookie(request: Request, response: Response) -> None:
    response.set_cookie(
        AUTH_COOKIE_NAME,
        settings.internal_api_key,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )


class InternalAuthMiddleware(BaseHTTPMiddleware):
    """Require STUDIO_INTERNAL_API_KEY on operator routes."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not _is_protected(request.url.path):
            response = await call_next(request)
            if request.method == "GET" and _accepts_html(request):
                _set_browser_auth_cookie(request, response)
            return response

        provided = _extract_api_key(request)
        if provided != settings.internal_api_key:
            if _accepts_html(request) or request.headers.get("hx-request"):
                return Response(
                    content="Unauthorized — set Authorization: Bearer {STUDIO_INTERNAL_API_KEY}",
                    status_code=401,
                    media_type="text/plain",
                )
            return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=401)
        response = await call_next(request)
        if request.method == "GET" and _accepts_html(request):
            _set_browser_auth_cookie(request, response)
        return response
