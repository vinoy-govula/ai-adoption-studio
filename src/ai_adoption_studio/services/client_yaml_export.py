"""Export client.yaml from lead assessment and branding state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ai_adoption_studio.services.store import LeadStore


def build_client_yaml_payload(
    *,
    lead_id: str,
    store: LeadStore,
    branding: dict[str, Any],
) -> dict[str, Any]:
    report = store.get_assessment_report(lead_id) or {}
    client = report.get("client", {})
    recommendation = report.get("recommendation", {})
    slug = branding.get("client_slug") or client.get("slug") or lead_id.replace("lead-", "")
    profile = recommendation.get("recommended_pack") or branding.get("profile") or "business"
    model = branding.get("production_model") or recommendation.get("production_model") or "qwen3-7b"
    preset = branding.get("playground_preset_key") or recommendation.get("playground_preset_key")

    capabilities = [
        {
            "name": "knowledge-chat",
            "description": "Organisational knowledge conversations",
            "default_model": model,
        },
        {
            "name": "summarization",
            "description": "Document summarization",
            "default_model": model,
        },
    ]

    edge_mode = "nginx" if branding.get("use_edge_overlay", True) else "none"
    return {
        "schema_version": "1.0",
        "client": {
            "slug": slug,
            "display_name": branding.get("display_name") or client.get("display_name", slug),
            "contact_email": client.get("contact", {}).get("email", f"ops@{slug}.local"),
        },
        "branding": {
            "logo_url": branding.get("logo_url", ""),
            "welcome_message": branding.get("welcome_message", ""),
        },
        "deployment": {
            "profile": profile,
            "model": model,
            "runtime": None,
            "defaults": {"ram_gb": 64, "vram_gb": 16},
            "validation_preset": preset,
        },
        "gateway": {"rate_limit_per_minute": 60},
        "capabilities": capabilities,
        "edge": {
            "mode": edge_mode,
            "public_url": branding.get("public_url", ""),
            "http_port": 80,
        },
        "bootstrap": {
            "admin_email": client.get("contact", {}).get("email", f"admin@{slug}.local"),
            "operator_name": f"{slug}-operator",
        },
    }


def export_client_yaml(
    *,
    lead_id: str,
    store: LeadStore,
    branding: dict[str, Any],
    output_path: Path | None = None,
) -> Path:
    payload = build_client_yaml_payload(lead_id=lead_id, store=store, branding=branding)
    lead_dir = store._store.lead_dir(lead_id)
    path = output_path or (lead_dir / "client.yaml")
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    meta = lead_dir / "client-yaml-export.json"
    meta.write_text(
        json.dumps({"lead_id": lead_id, "path": str(path), "delivery_mode": "single_config"}),
        encoding="utf-8",
    )
    return path
