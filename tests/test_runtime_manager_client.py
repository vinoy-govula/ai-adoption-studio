"""RuntimeManagerClient tests."""

import pytest

from ai_adoption_studio.adapters.runtime_manager_client import RuntimeManagerClient


@pytest.mark.asyncio
async def test_list_presets(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(path: str, params=None):  # noqa: ANN001
        assert path == "/api/v1/presets"
        return [{"platform_key": "gemma-e2b-gpu"}]

    client = RuntimeManagerClient(base_url="http://localhost:8001")
    monkeypatch.setattr(client, "_get", fake_get)
    presets = await client.list_presets()
    assert presets[0]["platform_key"] == "gemma-e2b-gpu"


@pytest.mark.asyncio
async def test_get_recommendations(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(path: str, params=None):  # noqa: ANN001
        return {
            "default_production_model": "qwen3-7b",
            "default_validation_preset": "gemma-12b-gpu",
        }

    client = RuntimeManagerClient(base_url="http://localhost:8001")
    monkeypatch.setattr(client, "_get", fake_get)
    data = await client.get_recommendations("business")
    assert data["default_production_model"] == "qwen3-7b"
