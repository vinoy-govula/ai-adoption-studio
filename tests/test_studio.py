from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from ai_adoption_studio.config import settings
from ai_adoption_studio.main import app
from ai_adoption_studio.services.store import LeadStore


@pytest.fixture
def store(tmp_path: Path) -> LeadStore:
    return LeadStore(tmp_path)


@pytest.mark.asyncio
async def test_eoi_api_creates_lead(store: LeadStore, monkeypatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    payload = {
        "consent": {"privacy_policy_accepted": True, "contact_permitted": True},
        "responses": {"org_name": "Test Org", "industry": "healthcare"},
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/eoi", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    lead_id = body["data"]["lead_id"]
    saved = store.get_eoi(lead_id)
    assert saved["responses"]["org_name"] == "Test Org"


def test_lead_store_create_and_list(store: LeadStore) -> None:
    record = store.create_eoi(
        {
            "consent": {"privacy_policy_accepted": True, "contact_permitted": True},
            "responses": {"org_name": "Acme"},
        }
    )
    leads = store.list_leads()
    assert any(item["lead_id"] == record["lead_id"] for item in leads)
    path = store._store.lead_dir(record["lead_id"]) / "eoi-intent.json"
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["responses"]["org_name"] == "Acme"


def test_lead_store_archives_incomplete_leads(store: LeadStore, tmp_path: Path) -> None:
    stale = tmp_path / "lead-20260621-4aefea"
    stale.mkdir()

    assert store.list_leads() == []
    assert store.cleanup_incomplete_leads() == ["lead-20260621-4aefea"]
    assert not stale.exists()
    assert (tmp_path / ".incomplete-leads" / "lead-20260621-4aefea").exists()


@pytest.mark.asyncio
async def test_legacy_lead_redirects_to_wizard(store: LeadStore, monkeypatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    record = store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "Acme"}}
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as client:
        resp = await client.get(f"/leads/{record['lead_id']}")
    assert resp.status_code == 302
    assert f"/wizard/{record['lead_id']}" in resp.headers["location"]


@pytest.mark.asyncio
async def test_inbox_lists_leads(store: LeadStore, monkeypatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    record = store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "Inbox Co"}}
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    assert "Inbox Co" in resp.text
    assert "Start blank EOI" in resp.text
    assert f"/eoi/{record['lead_id']}" in resp.text
    assert "hx-boost" in resp.text
    assert "Authorization" in resp.text
    assert f"Bearer {settings.internal_api_key}" in resp.text


@pytest.mark.asyncio
async def test_open_existing_eoi_from_inbox(store: LeadStore, monkeypatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    record = store.create_eoi(
        {
            "consent": {"privacy_policy_accepted": True, "contact_permitted": True},
            "responses": {
                "org_name": "Existing Co",
                "industry": "finance",
                "contact_email": "owner@example.com",
                "contact_name": "Owner",
                "intent": "explore",
            },
        }
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as client:
        resp = await client.post("/eoi-open", data={"lead_id": record["lead_id"]})
    assert resp.status_code == 302
    assert f"/eoi/{record['lead_id']}" in resp.headers["location"]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/eoi/{record['lead_id']}")
    assert resp.status_code == 200
    assert "Existing Co" in resp.text


@pytest.mark.asyncio
async def test_existing_eoi_form_updates_record(store: LeadStore, monkeypatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    record = store.create_eoi(
        {
            "consent": {"privacy_policy_accepted": True, "contact_permitted": True},
            "responses": {
                "org_name": "Old Co",
                "industry": "healthcare",
                "contact_email": "old@example.com",
                "contact_name": "Old Owner",
                "intent": "deploy",
            },
        }
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/eoi/{record['lead_id']}",
            data={
                "org_name": "Updated Co",
                "industry": "finance",
                "contact_email": "new@example.com",
                "contact_name": "New Owner",
                "intent": "explore",
                "privacy_policy_accepted": "true",
                "contact_permitted": "true",
            },
        )
    assert resp.status_code == 200
    updated = store.get_eoi(record["lead_id"])
    assert updated["responses"]["org_name"] == "Updated Co"
    assert updated["eoi_id"] == record["eoi_id"]


@pytest.mark.asyncio
async def test_existing_eoi_page_bootstraps_wizard_auth_cookie(store: LeadStore, monkeypatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.services.wizard_service.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._wizard._store", store)
    record = store.create_eoi(
        {
            "consent": {"privacy_policy_accepted": True, "contact_permitted": True},
            "responses": {
                "org_name": "Cookie Co",
                "industry": "finance",
                "contact_email": "owner@example.com",
                "contact_name": "Owner",
                "intent": "explore",
            },
        }
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Accept": "text/html"},
    ) as client:
        eoi_resp = await client.get(f"/eoi/{record['lead_id']}")
        assert eoi_resp.status_code == 200
        assert client.cookies.get("studio_api_key") == "dev-key"
        assert "hx-boost" in eoi_resp.text
        assert "Authorization" in eoi_resp.text
        assert f"Bearer {settings.internal_api_key}" in eoi_resp.text

        wizard_resp = await client.get(f"/wizard/{record['lead_id']}")

    assert wizard_resp.status_code == 200
    assert "Wizard" in wizard_resp.text
