from __future__ import annotations

from ai_adoption_studio.services.infrastructure_urls import resolve_urls


def test_resolve_urls_developer_defaults() -> None:
    urls = resolve_urls(None)
    assert urls.infrastructure_stage == "developer"
    assert urls.gateway_base_url == "http://localhost:8000"
    assert urls.control_centre_url == "http://localhost:8002"
    assert urls.use_edge_routing is False


def test_resolve_urls_playground_with_edge() -> None:
    manifest = {
        "access": {
            "public_url": "https://playground-acme.example.com",
            "control_centre_path": "/control-centre",
        },
        "deployment": {
            "infrastructure_stage": "playground",
            "edge_profile": "platform-overlay",
        },
    }
    urls = resolve_urls(manifest)
    assert urls.gateway_base_url == "https://playground-acme.example.com"
    assert urls.gateway_health_url == "https://playground-acme.example.com/healthz"
    assert urls.control_centre_url == "https://playground-acme.example.com/control-centre"
    assert urls.use_edge_routing is True
