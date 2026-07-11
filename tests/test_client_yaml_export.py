import json
from pathlib import Path

import yaml

from ai_adoption_studio.services.client_yaml_export import build_client_yaml_payload, export_client_yaml
from ai_adoption_studio.services.store import LeadStore


def test_build_client_yaml_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STUDIO_DATA_ROOT", str(tmp_path))
    store = LeadStore(root=tmp_path)
    lead_id = "lead-test-001"
    store._store.write_json(
        lead_id,
        "assessment-report.json",
        {
            "client": {"slug": "acme", "display_name": "ACME", "contact": {"email": "ops@acme.com"}},
            "recommendation": {"recommended_pack": "business", "production_model": "qwen3-7b"},
        },
    )
    branding = {
        "client_slug": "acme",
        "display_name": "ACME",
        "production_model": "qwen3-7b",
        "public_url": "https://ai.acme.com",
        "use_edge_overlay": True,
    }
    payload = build_client_yaml_payload(lead_id=lead_id, store=store, branding=branding)
    assert payload["client"]["slug"] == "acme"
    assert payload["deployment"]["model"] == "qwen3-7b"


def test_export_client_yaml_writes_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STUDIO_DATA_ROOT", str(tmp_path))
    store = LeadStore(root=tmp_path)
    lead_id = "lead-test-002"
    store._store.write_json(lead_id, "assessment-report.json", {"client": {"slug": "demo"}})
    branding = {"client_slug": "demo", "display_name": "Demo", "production_model": "qwen3-7b"}
    path = export_client_yaml(lead_id=lead_id, store=store, branding=branding)
    assert path.exists()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    meta = json.loads((path.parent / "client-yaml-export.json").read_text(encoding="utf-8"))
    assert meta["delivery_mode"] == "single_config"
