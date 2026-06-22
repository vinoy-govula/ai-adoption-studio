"""Golden path wizard flow with mocked adapters."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from ai_adoption_studio.main import app
from ai_adoption_studio.models.certification_verdict import CertificationVerdict
from ai_adoption_studio.services.store import LeadStore


@pytest.fixture
def store(tmp_path: Path) -> LeadStore:
    return LeadStore(tmp_path)


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer dev-key"}


@pytest.mark.asyncio
async def test_golden_path_wizard_steps(store: LeadStore, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.services.wizard_service.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._wizard._store", store)

    record = store.create_eoi(
        {
            "consent": {"privacy_policy_accepted": True, "contact_permitted": True},
            "responses": {"org_name": "Golden Org", "industry": "healthcare"},
        }
    )
    lead_id = record["lead_id"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=_auth_headers()) as client:
        resp = await client.get(f"/wizard/{lead_id}")
        assert resp.status_code == 200
        assert "step-content" in resp.text or "Wizard" in resp.text

        resp = await client.post(f"/wizard/{lead_id}/eoi_review", data={"acknowledged": "true"})
        assert resp.status_code == 200

        resp = await client.post(f"/wizard/{lead_id}/qualify", data={"actor": "sales@example.com"})
        assert resp.status_code == 200

    internal = {
        "executive_sponsor_identified": "true",
        "ai_strategy_documented": "draft",
        "document_corpus_ready": "partially_curated",
        "data_classification_in_place": "true",
        "compliance_frameworks": "privacy_act",
        "audit_retention_requirement": "90_days",
        "it_ops_capacity": "moderate",
        "deployment_target": "private_cloud",
        "concurrent_users": "25",
        "daily_requests": "8000",
        "target_latency_ms": "3000",
        "change_champion_identified": "true",
        "staff_ai_literacy": "moderate",
    }

    async with AsyncClient(transport=transport, base_url="http://test", headers=_auth_headers()) as client:
        resp = await client.post(f"/wizard/{lead_id}/assessment_form", data=internal)
        assert resp.status_code == 200

        resp = await client.post(f"/wizard/{lead_id}/assessment_run")
        assert resp.status_code == 200

    report_path = store._store.lead_dir(lead_id) / "assessment-report.json"
    assert report_path.exists()

    mock_client = MagicMock()
    mock_client.chat = MagicMock(return_value={"content": "ok"})

    with patch("ai_adoption_studio.adapters.delivery_validator.DeploymentOrchestrator.generate_kit", new_callable=AsyncMock) as gen_kit:
        gen_kit.return_value = store._store.lead_dir(lead_id) / "playground-kit.manifest.json"

        async with AsyncClient(transport=transport, base_url="http://test", headers=_auth_headers()) as client:
            await client.post(f"/wizard/{lead_id}/narrative")
            await client.post(
                f"/wizard/{lead_id}/cp2_approve",
                data={"actor": "client@example.com", "notes": "approved"},
            )

            manifest = {
                "schema_version": "1.0.0",
                "manifest_id": "test",
                "status": "draft",
                "validation": {},
            }
            manifest_path = store._store.lead_dir(lead_id) / "playground-kit.manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            await client.post(
                f"/wizard/{lead_id}/branding_kit",
                data={
                    "client_slug": "golden",
                    "display_name": "Golden Org",
                    "welcome_message": "Hi",
                    "logo_url": "",
                    "public_url": "http://localhost:8000",
                    "ttl_days": "30",
                },
            )

    with patch(
        "ai_adoption_studio.adapters.delivery_validator.DeploymentOrchestrator.deploy_lab",
        new_callable=AsyncMock,
        return_value=0,
    ):
        async with AsyncClient(transport=transport, base_url="http://test", headers=_auth_headers()) as client:
            manifest_path = store._store.lead_dir(lead_id) / "playground-kit.manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "draft"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            await client.post(f"/api/leads/{lead_id}/deploy")

    with patch("ai_adoption_studio.services.smoke_test_service.SmokeTestService.run", new_callable=AsyncMock) as smoke_run:
        from ai_adoption_studio.models.workflow_state import SmokeResult

        smoke_run.return_value = SmokeResult(status="passed", latency_ms=100, message="ok")
        async with AsyncClient(transport=transport, base_url="http://test", headers=_auth_headers()) as client:
            await client.post(f"/api/leads/{lead_id}/smoke-test", data={"test_capability": "chat"})

    with patch(
        "ai_adoption_studio.services.certification_service.CertificationService.certify",
        new_callable=AsyncMock,
        return_value=CertificationVerdict(verdict="pass", confidence=0.9),
    ):
        async with AsyncClient(transport=transport, base_url="http://test", headers=_auth_headers()) as client:
            resp = await client.post(f"/api/leads/{lead_id}/cursor/certify")
            assert resp.status_code == 200
            assert "pass" in resp.text.lower()


@pytest.mark.asyncio
async def test_wizard_requires_auth(store: LeadStore, monkeypatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    record = store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "X"}}
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/wizard/{record['lead_id']}")
        assert resp.status_code == 401
