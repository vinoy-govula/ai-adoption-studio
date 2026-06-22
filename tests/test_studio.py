from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

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
    store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "Inbox Co"}}
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    assert "Inbox Co" in resp.text
