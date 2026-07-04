"""Resolve Gateway and Control Centre URLs from manifest and infrastructure stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_adoption_studio.config import settings


@dataclass(frozen=True)
class InfrastructureUrls:
    infrastructure_stage: str
    edge_profile: str
    gateway_base_url: str
    gateway_health_url: str
    control_centre_url: str
    control_centre_health_url: str
    runtime_manager_url: str
    use_edge_routing: bool


def _gateway_base_from_access(access: dict[str, Any]) -> str:
    public_url = access.get("public_url", settings.gateway_base_url).rstrip("/")
    api_path = access.get("gateway_api_path", "/api/v1").rstrip("/")
    if public_url.endswith(api_path):
        return public_url[: -len(api_path)]
    return public_url


def infrastructure_stage_from_manifest(manifest: dict[str, Any] | None) -> str:
    if not manifest:
        return "developer"
    deployment = manifest.get("deployment", {})
    return str(deployment.get("infrastructure_stage", "developer"))


def edge_profile_from_manifest(manifest: dict[str, Any] | None) -> str:
    if not manifest:
        return "none"
    deployment = manifest.get("deployment", {})
    return str(deployment.get("edge_profile", "none"))


def resolve_urls(manifest: dict[str, Any] | None = None) -> InfrastructureUrls:
    """Resolve poll and deep-link URLs for the current infrastructure stage."""
    stage = infrastructure_stage_from_manifest(manifest)
    edge_profile = edge_profile_from_manifest(manifest)

    if stage == "developer" or manifest is None:
        gateway_base = settings.gateway_base_url.rstrip("/")
        cc_base = settings.control_centre_base_url.rstrip("/")
        return InfrastructureUrls(
            infrastructure_stage=stage,
            edge_profile=edge_profile,
            gateway_base_url=gateway_base,
            gateway_health_url=f"{gateway_base}/healthz",
            control_centre_url=cc_base,
            control_centre_health_url=f"{cc_base}/healthz",
            runtime_manager_url=settings.runtime_manager_base_url.rstrip("/"),
            use_edge_routing=False,
        )

    access = manifest.get("access", {})
    gateway_base = _gateway_base_from_access(access)
    cc_path = access.get("control_centre_path", "/control-centre").rstrip("/")
    if not cc_path.startswith("/"):
        cc_path = f"/{cc_path}"

    use_edge = edge_profile == "platform-overlay" or stage in {"playground", "production_preview"}
    cc_public = f"{gateway_base}{cc_path}".replace("//", "/").replace(":/", "://")

    return InfrastructureUrls(
        infrastructure_stage=stage,
        edge_profile=edge_profile,
        gateway_base_url=gateway_base,
        gateway_health_url=f"{gateway_base}/healthz",
        control_centre_url=cc_public,
        control_centre_health_url=f"{cc_public}/healthz".replace("//", "/").replace(":/", "://"),
        runtime_manager_url=settings.runtime_manager_base_url.rstrip("/"),
        use_edge_routing=use_edge,
    )


def load_manifest_from_path(manifest_path: Any) -> dict[str, Any] | None:
    import json
    from pathlib import Path

    path = Path(manifest_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
