"""Certified preset and production model picker (playground kit step)."""

from __future__ import annotations

from typing import Any

from fasthtml.common import A, Details, Div, FT, H4, Li, P, Summary, Ul
from monsterui.all import Alert, AlertT, Card, LabelRadio

from ai_adoption_studio.components.model_card_summary import model_card_summary
from ai_adoption_studio.components.parity_banner import parity_banner
from ai_adoption_studio.config import settings


def catalog_unavailable_banner(*, error: str | None = None, empty: bool = False) -> FT:
    if empty:
        return Alert(
            Div(
                P("Runtime Manager is reachable but has no certified presets or production models."),
                Ul(cls="list-disc ml-5 mt-2 text-sm")(
                    Li("Build and lab-validate models in Open LLM Workbench"),
                    Li("Promote lab-validated cards to Runtime Manager"),
                    Li("Refresh this step after promotion completes"),
                ),
                A(
                    "Open Workbench →",
                    href=settings.workbench_url,
                    target="_blank",
                    cls="underline text-blue-700 mt-2 inline-block",
                ),
            ),
            cls=AlertT.warning,
        )
    detail = error or "Connection failed"
    return Alert(
        Div(
            P(f"Certified catalog unavailable ({detail})."),
            Ul(cls="list-disc ml-5 mt-2 text-sm")(
                Li(f"Verify STUDIO_RUNTIME_MANAGER_BASE_URL ({settings.runtime_manager_base_url})"),
                Li("Start Runtime Manager and confirm GET /healthz returns 200"),
                Li("Promote lab-validated models from Workbench when RM is up"),
            ),
            A(
                "Open Workbench →",
                href=settings.workbench_url,
                target="_blank",
                cls="underline text-blue-700 mt-2 inline-block",
            ),
        ),
        cls=AlertT.warning,
    )


def _radio_option(
    *,
    name: str,
    key: str,
    label: str,
    selected: str,
    disabled: bool,
    tooltip: str,
    summary_entry: dict[str, Any],
) -> FT:
    return Div(
        LabelRadio(
            label,
            name=name,
            value=key,
            checked=selected == key,
            disabled=disabled,
            title=tooltip,
        ),
        model_card_summary(summary_entry, compact=True),
        cls="rounded border border-slate-200 bg-slate-50 p-2",
    )


def _build_options(
    *,
    items: list[dict[str, Any]],
    key_field: str,
    input_name: str,
    selected: str,
    recommended_key: str,
    label_field: str,
    lab_vram_gb: float | None,
) -> list[FT]:
    options: list[FT] = []
    for item in items:
        key = item.get(key_field, "")
        disabled = False
        tooltip = ""
        vram = item.get("vram_gb")
        if lab_vram_gb is not None and vram and vram > lab_vram_gb:
            disabled = True
            tooltip = f"Requires {vram} GB VRAM"
        label = str(item.get(label_field) or key)
        if key == recommended_key:
            label += " ★ Recommended"
        options.append(
            _radio_option(
                name=input_name,
                key=key,
                label=label,
                selected=selected,
                disabled=disabled,
                tooltip=tooltip,
                summary_entry=item,
            )
        )
    return options


def certified_model_picker(
    lead_id: str,
    *,
    presets: list[dict[str, Any]],
    models: list[dict[str, Any]],
    suggested_presets: list[dict[str, Any]] | None = None,
    suggested_models: list[dict[str, Any]] | None = None,
    selected_preset: str,
    selected_model: str,
    recommended_preset: str,
    recommended_model: str,
    lab_vram_gb: float | None = None,
) -> FT:
    suggested_presets = suggested_presets or presets
    suggested_models = suggested_models or models
    preset_options = _build_options(
        items=suggested_presets,
        key_field="platform_key",
        input_name="playground_preset_key",
        selected=selected_preset,
        recommended_key=recommended_preset,
        label_field="display_name",
        lab_vram_gb=lab_vram_gb,
    )
    model_options = _build_options(
        items=suggested_models,
        key_field="model",
        input_name="production_model",
        selected=selected_model,
        recommended_key=recommended_model,
        label_field="display_name",
        lab_vram_gb=lab_vram_gb,
    )
    extra_presets = [item for item in presets if item.get("platform_key") not in {p.get("platform_key") for p in suggested_presets}]
    extra_models = [item for item in models if item.get("model") not in {m.get("model") for m in suggested_models}]
    can_generate = bool(presets and models and selected_preset and selected_model)

    return Card(
        H4("Certified model selection", cls="font-semibold mb-2"),
        Div(cls="text-sm mb-3")(
            "Models are certified in Open LLM Workbench and published to Runtime Manager. ",
            A("Manage models →", href=settings.workbench_url, target="_blank", cls="underline text-blue-700"),
        ),
        Div(cls="grid lg:grid-cols-2 gap-4")(
            Div(
                P("PLAYGROUND PRESET (lab validation)", cls="text-sm font-medium mb-2"),
                Div(cls="grid gap-2")(*preset_options)
                if preset_options
                else P("No suggested presets available.", cls="text-sm text-slate-600"),
                Details(
                    Summary("All certified presets", cls="cursor-pointer text-xs text-blue-700 mt-2"),
                    Div(cls="grid gap-2 mt-2")(
                        *_build_options(
                            items=extra_presets,
                            key_field="platform_key",
                            input_name="playground_preset_key",
                            selected=selected_preset,
                            recommended_key=recommended_preset,
                            label_field="display_name",
                            lab_vram_gb=lab_vram_gb,
                        )
                    )
                    if extra_presets
                    else P("All certified presets are already shown above.", cls="text-xs text-slate-500 mt-2"),
                ),
            ),
            Div(
                P("PRODUCTION TARGET (client go-live)", cls="text-sm font-medium mb-2"),
                Div(cls="grid gap-2")(*model_options)
                if model_options
                else P("No suggested production models available.", cls="text-sm text-slate-600"),
                Details(
                    Summary("All certified models", cls="cursor-pointer text-xs text-blue-700 mt-2"),
                    Div(cls="grid gap-2 mt-2")(
                        *_build_options(
                            items=extra_models,
                            key_field="model",
                            input_name="production_model",
                            selected=selected_model,
                            recommended_key=recommended_model,
                            label_field="display_name",
                            lab_vram_gb=lab_vram_gb,
                        )
                    )
                    if extra_models
                    else P("All certified models are already shown above.", cls="text-xs text-slate-500 mt-2"),
                ),
            ),
        ),
        parity_banner(preset_key=selected_preset, production_model=selected_model),
        P(
            "Select both a preset and production model before generating the playground manifest."
            if not can_generate
            else "",
            cls="text-sm text-amber-700 mt-2",
        ),
        cls="mb-4",
    )
