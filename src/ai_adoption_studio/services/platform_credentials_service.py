"""Provision and resolve per-lead Gateway credentials at deploy time."""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from ai_adoption_studio.config import settings
from ai_adoption_studio.models.platform_credentials import (
    LabUserCredential,
    OperatorCredential,
    PlatformCredentials,
)
from ai_adoption_studio.services.infrastructure_urls import resolve_urls
from ai_adoption_studio.services.wizard_service import WizardService


class PlatformCredentialsService:
    """Create lab super-user + operator API key via Gateway admin APIs."""

    CREDENTIALS_FILE = "platform-credentials.json"

    def __init__(self, wizard: WizardService | None = None) -> None:
        self._wizard = wizard or WizardService()

    def credentials_path(self, lead_id: str) -> Path:
        return self._wizard._lead_dir(lead_id) / self.CREDENTIALS_FILE

    def load(self, lead_id: str) -> PlatformCredentials | None:
        path = self.credentials_path(lead_id)
        if not path.exists():
            return None
        return PlatformCredentials.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save(self, lead_id: str, credentials: PlatformCredentials) -> None:
        path = self.credentials_path(lead_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(credentials.model_dump_json(indent=2), encoding="utf-8")
        self._update_manifest_metadata(lead_id, credentials)

    def resolve_operator_api_key(self, lead_id: str) -> str | None:
        credentials = self.load(lead_id)
        if credentials is not None:
            return credentials.operator.api_key
        return None

    def admin_key_source(self) -> tuple[str | None, str | None]:
        if settings.gateway_admin_key:
            return settings.gateway_admin_key, "STUDIO_GATEWAY_ADMIN_KEY"
        if settings.platform_api_key:
            return settings.platform_api_key, "STUDIO_PLATFORM_API_KEY"
        env_path = settings.deployment_catalog_root / ".env"
        if env_path.exists():
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == "GATEWAY_API_KEY" and value.strip():
                    return value.strip(), "deployment-catalog/.env:GATEWAY_API_KEY"
        return None, None

    def admin_api_key(self) -> str:
        key, source = self.admin_key_source()
        if not key:
            raise RuntimeError(
                "Configure STUDIO_GATEWAY_ADMIN_KEY, STUDIO_PLATFORM_API_KEY, or "
                "deployment-catalog/.env GATEWAY_API_KEY to provision lab credentials."
            )
        return key

    def admin_api_key_hint(self) -> str:
        _, source = self.admin_key_source()
        if source:
            return source
        return "not configured"

    def _update_manifest_metadata(self, lead_id: str, credentials: PlatformCredentials) -> None:
        manifest_path = self._wizard._lead_dir(lead_id) / WizardService.MANIFEST_FILE
        if not manifest_path.exists():
            return
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        access = manifest.setdefault("access", {})
        access["credentials_ref"] = self.CREDENTIALS_FILE
        access["operator_key_prefix"] = credentials.operator.key_prefix
        access["super_user_username"] = credentials.super_user.username
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def _client_slug(self, lead_id: str) -> str:
        manifest_path = self._wizard._lead_dir(lead_id) / WizardService.MANIFEST_FILE
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            slug = manifest.get("client", {}).get("slug")
            if isinstance(slug, str) and slug.strip():
                return slug.strip().lower().replace(" ", "-")
        return lead_id.replace("lead-", "")

    async def provision(self, lead_id: str, *, force: bool = False) -> PlatformCredentials:
        existing = self.load(lead_id)
        if existing is not None and not force:
            return existing

        manifest_path = self._wizard._lead_dir(lead_id) / WizardService.MANIFEST_FILE
        if not manifest_path.exists():
            raise FileNotFoundError("Playground manifest missing; generate kit before deploy.")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        gateway_base = settings.gateway_base_url.rstrip("/")
        slug = self._client_slug(lead_id)
        admin_key = self.admin_api_key()

        super_username = f"{slug}-lab-admin"
        operator_username = f"{slug}-operator"
        super_password = secrets.token_urlsafe(18)
        operator_password = secrets.token_urlsafe(18)

        async with httpx.AsyncClient(base_url=gateway_base, timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {admin_key}", "Accept": "application/json"}
            super_user = await self._create_user(
                client,
                headers,
                username=super_username,
                email=f"{super_username}@lab.local",
                password=super_password,
                role="platform_administrator",
            )
            operator_user = await self._create_user(
                client,
                headers,
                username=operator_username,
                email=f"{operator_username}@lab.local",
                password=operator_password,
                role="developer",
            )
            operator_key = await self._create_api_key(
                client,
                headers,
                name=f"{lead_id}-operator",
                user_id=operator_user["id"],
            )

        credentials = PlatformCredentials(
            lead_id=lead_id,
            gateway_base_url=gateway_base,
            provisioned_at=datetime.now(UTC).isoformat(),
            super_user=LabUserCredential(
                username=super_username,
                email=f"{super_username}@lab.local",
                role="platform_administrator",
                password=super_password,
            ),
            operator=OperatorCredential(
                username=operator_username,
                email=f"{operator_username}@lab.local",
                api_key=operator_key["key"],
                key_prefix=operator_key["key_prefix"],
                user_id=operator_user["id"],
            ),
        )
        self.save(lead_id, credentials)
        return credentials

    async def _create_user(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        *,
        username: str,
        email: str,
        password: str,
        role: str,
    ) -> dict[str, Any]:
        response = await client.post(
            "/api/v1/users",
            json={"username": username, "email": email, "password": password, "role": role},
            headers=headers,
        )
        if response.status_code == 401:
            raise RuntimeError(
                "Gateway admin key was rejected while provisioning lab credentials. "
                "Use the same bootstrap key for the running Gateway and Studio "
                "(STUDIO_GATEWAY_ADMIN_KEY or deployment-catalog/.env GATEWAY_API_KEY)."
            )
        if response.status_code == 409:
            raise RuntimeError(f"Gateway user '{username}' already exists; delete or use force reprovision.")
        response.raise_for_status()
        body = response.json()
        data = body.get("data", body)
        if not isinstance(data, dict) or "id" not in data:
            raise RuntimeError(f"Unexpected Gateway user response for {username}")
        return data

    async def _create_api_key(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        *,
        name: str,
        user_id: str,
    ) -> dict[str, Any]:
        response = await client.post(
            "/api/v1/api-keys",
            json={"name": name, "user_id": user_id},
            headers=headers,
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data", body)
        if not isinstance(data, dict) or not data.get("key"):
            raise RuntimeError("Gateway did not return a new API key")
        return data


platform_credentials_service = PlatformCredentialsService()
