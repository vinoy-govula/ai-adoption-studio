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
        models = await client.list_models(status="certified")
    except Exception as exc:
        return {
            "presets": [],
            "models": [],
            "recommendations": {},
            "available": False,
            "error": str(exc),
            "empty": False,
            "suggested_presets": [],
            "suggested_models": [],
        }
    suggested_preset_keys = set(recommendations.get("validation_presets") or [])
    suggested_model_keys = set(recommendations.get("production_models") or [])
    suggested_presets = [preset for preset in presets if preset.get("platform_key") in suggested_preset_keys]
    suggested_models = [model for model in models if model.get("model") in suggested_model_keys]
    return {
        "presets": presets,
        "models": models,
        "recommendations": recommendations,
        "available": True,
        "error": None,
        "empty": not presets and not models,
        "suggested_presets": suggested_presets,
        "suggested_models": suggested_models,
    }


def find_preset(presets: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    return next((p for p in presets if p.get("platform_key") == key), None)


def find_model(models: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    return next((m for m in models if m.get("model") == key), None)
