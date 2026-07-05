"""Compact Model Card summary for wizard."""

from __future__ import annotations

from typing import Any

from fasthtml.common import Div, FT, P, Span
from monsterui.all import Card


def model_card_summary(entry: dict[str, Any], *, compact: bool = False) -> FT:
    key = entry.get("platform_key") or entry.get("model", "")
    display = entry.get("display_name") or key
    vram = entry.get("vram_gb")
    caps = entry.get("capabilities") or []
    backend = entry.get("runtime_backend") or entry.get("runtime", "")
    license_name = entry.get("license_spdx") or "—"
    packaging = entry.get("packaging") or {}
    image = packaging.get("docker_image", "")

    body = [
        P(display, cls="font-semibold"),
        P(f"Backend: {backend} · VRAM: {vram if vram is not None else 'CPU'} GB", cls="text-sm text-slate-600"),
    ]
    if caps:
        body.append(
            Div(cls="flex flex-wrap gap-1 mt-1")(
                *[Span(c, cls="text-xs bg-slate-200 rounded px-2 py-0.5") for c in caps]
            )
        )
    if not compact:
        body.extend(
            [
                P(f"License: {license_name}", cls="text-xs text-slate-500 mt-1"),
                P(f"Image: {image or 'n/a'}", cls="text-xs text-slate-500 truncate"),
            ]
        )
    return Card(*body, cls="bg-slate-50 p-3")
