"""Certified model picker component tests."""

from ai_adoption_studio.components.certified_model_picker import certified_model_picker
from ai_adoption_studio.components.parity_banner import parity_banner


def test_parity_banner_warns_on_mismatch() -> None:
    banner = parity_banner(preset_key="gemma-12b-gpu", production_model="qwen3-7b")
    assert banner is not None


def test_certified_model_picker_renders() -> None:
    html = certified_model_picker(
        "lead-1",
        presets=[
            {
                "platform_key": "gemma-e2b-gpu",
                "display_name": "Gemma E2B",
                "vram_gb": 4,
                "capabilities": ["chat"],
                "runtime_backend": "gpu_vllm",
            }
        ],
        models=[
            {
                "model": "qwen3-7b",
                "display_name": "Qwen3 7B",
                "vram_gb": 16,
                "capabilities": ["chat"],
                "runtime": "vllm",
            }
        ],
        selected_preset="gemma-e2b-gpu",
        selected_model="qwen3-7b",
        recommended_preset="gemma-e2b-gpu",
        recommended_model="qwen3-7b",
    )
    assert html is not None
