"""Tests for deploy-time platform credential provisioning."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ai_adoption_studio.models.platform_credentials import PlatformCredentials
from ai_adoption_studio.services.platform_credentials_service import PlatformCredentialsService


@pytest.fixture
def lead_dir(tmp_path, monkeypatch):
    lead_id = "lead-test-001"
    root = tmp_path / lead_id
    root.mkdir()
    manifest = {
        "status": "active",
        "client": {"slug": "acme"},
        "access": {"public_url": "http://localhost:8000"},
        "deployment": {"infrastructure_stage": "playground", "edge_profile": "platform-overlay"},
    }
    (root / "playground-kit.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    class FakeStore:
        def lead_dir(self, _: str):
            return root

    class FakeWizard:
        MANIFEST_FILE = "playground-kit.manifest.json"

        def _lead_dir(self, _: str):
            return root

    svc = PlatformCredentialsService(FakeWizard())
    monkeypatch.setattr(
        "ai_adoption_studio.services.platform_credentials_service.settings.gateway_admin_key",
        "sk-admin",
    )
    return lead_id, svc


@pytest.mark.asyncio
async def test_provision_creates_credentials_file(lead_dir):
    lead_id, svc = lead_dir
    user_ids = iter(["user-admin", "user-operator"])

    async def fake_post(url, json=None, headers=None):
        class Resp:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                if url.endswith("/users"):
                    return {"success": True, "data": {"id": next(user_ids), **json}}
                return {
                    "success": True,
                    "data": {"id": "key-1", "name": json["name"], "key_prefix": "sk-test01", "key": "sk-test-full"},
                }

        return Resp()

    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=fake_post)):
        creds = await svc.provision(lead_id)

    assert creds.operator.api_key == "sk-test-full"
    assert creds.super_user.username == "acme-lab-admin"
    assert svc.credentials_path(lead_id).exists()
    manifest = json.loads((svc.credentials_path(lead_id).parent / "playground-kit.manifest.json").read_text())
    assert manifest["access"]["operator_key_prefix"] == "sk-test01"


def test_resolve_operator_api_key_prefers_lead_credentials(lead_dir):
    lead_id, svc = lead_dir
    svc.save(
        lead_id,
        PlatformCredentials(
            lead_id=lead_id,
            gateway_base_url="http://localhost",
            provisioned_at="2026-01-01T00:00:00+00:00",
            super_user={
                "username": "a",
                "email": "a@x",
                "role": "platform_administrator",
                "password": "p",
            },
            operator={
                "username": "o",
                "email": "o@x",
                "api_key": "sk-lead-operator",
                "key_prefix": "sk-lead",
            },
        ),
    )
    assert svc.resolve_operator_api_key(lead_id) == "sk-lead-operator"
