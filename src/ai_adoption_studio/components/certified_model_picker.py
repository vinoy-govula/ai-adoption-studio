"""Certified preset and production model picker (playground kit step)."""

from __future__ import annotations

from typing import Any

from fasthtml.common import A, Div, FT, H4, P
from monsterui.all import Card, LabelRadio

from ai_adoption_studio.components.model_card_summary import model_card_summary
from ai_adoption_studio.components.parity_banner import parity_banner
from ai_adoption_studio.config import settings


def certified_model_picker(
    lead_id: str,
    *,
    presets: list[dict[str, Any]],
    models: list[dict[str, Any]],
    selected_preset: str,
    selected_model: str,
    recommended_preset: str,
    recommended_model: str,
    lab_vram_gb: float | None = None,
) -> FT:
    preset_options = []
    for preset in presets:
        key = preset.get("platform_key", "")
        disabled = False
        tooltip = ""
        vram = preset.get("vram_gb")
        if lab_vram_gb is not None and vram and vram > lab_vram_gb:
            disabled = True
            tooltip = f"Requires {vram} GB VRAM"
        label = f"{preset.get('display_name', key)}"
        if key == recommended_preset:
            label += " ★ Recommended"
        preset_options.append(
            Div(
                LabelRadio(
                    label,
                    name="playground_preset_key",
                    value=key,
                    checked=selected_preset == key,
                    disabled=disabled,
                    title=tooltip,
                ),
                model_card_summary(preset, compact=True) if selected_preset == key else "",
                cls="mb-2",
            )
        )

    model_options = []
    for model in models:
        key = model.get("model", "")
        disabled = False
        tooltip = ""
        vram = model.get("vram_gb")
        if lab_vram_gb is not None and vram and vram > lab_vram_gb:
            disabled = True
            tooltip = f"Requires {vram} GB VRAM"
        label = f"{model.get('display_name') or key}"
        if key == recommended_model:
            label += " ★ Recommended"
        model_options.append(
            Div(
                LabelRadio(
                    label,
                    name="production_model",
                    value=key,
                    checked=selected_model == key,
                    disabled=disabled,
                    title=tooltip,
                ),
                model_card_summary(model, compact=True) if selected_model == key else "",
                cls="mb-2",
            )
        )

    return Card(
        H4("Certified model selection", cls="font-semibold mb-2"),
        Div(cls="text-sm mb-3")(
            "Models are certified in Open LLM Workbench. ",
            A("Manage models →", href=settings.workbench_url, target="_blank", cls="underline text-blue-700"),
        ),
        P("PLAYGROUND PRESET (lab validation)", cls="text-sm font-medium mt-3 mb-1"),
        Div(cls="flex flex-col gap-1 mb-4")(*preset_options),
        P("PRODUCTION TARGET (client go-live)", cls="text-sm font-medium mt-2 mb-1"),
        Div(cls="flex flex-col gap-1 mb-3")(*model_options),
        parity_banner(preset_key=selected_preset, production_model=selected_model),
        cls="mb-4",
    )
