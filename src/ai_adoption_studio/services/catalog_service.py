"""Runtime Manager catalog helpers for wizard."""

from __future__ import annotations

from typing import Any

from ai_adoption_studio.adapters.runtime_manager_client import RuntimeManagerClient


async def load_catalog_context(
    *,
    profile: str = "business",
    has_gpu: bool = True,
    vram_gb: float | None = None,
) -> dict[str, Any]:
    client = RuntimeManagerClient()
    try:
        recommendations = await client.get_recommendations(profile, has_gpu=has_gpu, vram_gb=vram_gb)
        presets = await client.list_presets(status="certified")
        models = await client.list_models(status="certified", profile=profile)
    except Exception:
        return {
            "presets": [],
            "models": [],
            "recommendations": {},
            "available": False,
        }
    return {
        "presets": presets,
        "models": models,
        "recommendations": recommendations,
        "available": True,
    }


def find_preset(presets: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    return next((p for p in presets if p.get("platform_key") == key), None)


def find_model(models: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    return next((m for m in models if m.get("model") == key), None)
