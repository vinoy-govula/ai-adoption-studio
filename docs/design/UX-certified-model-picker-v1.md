# UX — Certified Model Picker v1

**Status:** Accepted  
**Parent spec:** [SPEC-certified-model-picker-v1.md](./SPEC-certified-model-picker-v1.md)  
**Application form:** FastHTML + HTMX + MonsterUI

---

## 1. Step 7 wireframe — Playground kit

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ GoalBanner: Configure playground kit · ~10 min · Adoption engineer          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Certified model selection ──────────────────────────────────────────┐ │
│  │  ℹ Models are certified in Open LLM Workbench. [Manage models →]      │ │
│  │                                                                         │ │
│  │  PLAYGROUND PRESET (lab validation)                                    │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │ ● gemma-12b-gpu  ★ Recommended                                  │   │ │
│  │  │   Gemma 4 12B Instruct (AutoRound) · vLLM GPU · ~12 GB VRAM     │   │ │
│  │  │   Capabilities: chat, summarization · License: Gemma            │   │ │
│  │  │   Image: registry.example.com/ai/vllm-gemma4-unified:1.2.0      │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │  ○ gemma-e2b-gpu — faster demo · ~4 GB                                 │ │
│  │  ○ smol-cpu-llamacpp — CPU only, no GPU                                │ │
│  │                                                                         │ │
│  │  PRODUCTION TARGET (client go-live)                                    │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │ ● qwen3-7b  ★ Recommended for Business pack                      │   │ │
│  │  │   Qwen3 7B · vLLM · 16 GB VRAM · 32k context                    │   │ │
│  │  │   Capabilities: chat, sql-analysis, summarization               │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │  ○ gemma-3-27b — requires 24 GB (disabled: lab GPU insufficient)       │ │
│  │                                                                         │ │
│  │  ⚠ Parity: Lab uses gemma-12b-gpu. Production uses qwen3-7b on        │ │
│  │    client hardware. Re-validation required on client premises.         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ Branding ─────────────────────────────────────────────────────────────┐ │
│  │  Infrastructure stage: [Playground ▼]   ☑ Edge overlay               │ │
│  │  Logo URL: [________________________]                                   │ │
│  │  Welcome message: [________________________________]                  │ │
│  │  Public URL: [https://playground-acme.example.com]                    │ │
│  │  TTL days: [30]                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Path contract: /api/v1 · /control-centre · /healthz                        │
│                                                                             │
│  [← Back]  [Save draft]  [Generate manifest →]                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Interactions**

| Action | HTMX / behaviour |
|--------|------------------|
| Select preset radio | `hx-post` save selection; refresh `ModelCardSummary` + `ParityBanner` |
| Select production radio | Same; disable incompatible options (grey + tooltip) |
| "Manage models →" | External link to Workbench URL (`STUDIO_WORKBENCH_URL`) |
| "Generate manifest" | POST with selected keys; RM kit builder embeds certified packaging |
| Expand card detail | `Details/Summary` shows full operator notes from Model Card |

---

## 2. Step 4 wireframe — Assessment preview (read-only)

```text
┌─ Recommended models (certified catalog) ────────────────────┐
│  Assessment recommends Business pack                         │
│                                                              │
│  Lab preset:     gemma-12b-gpu                               │
│  Production:     qwen3-7b                                    │
│                                                              │
│  [ModelCardSummary — compact two-column]                     │
│                                                              │
│  You can change selections on Playground kit step.           │
└──────────────────────────────────────────────────────────────┘
```

Placed below `recommendation_card` on step 4.

---

## 3. Step 8 deploy preflight addition

```text
┌─ Deploy prerequisites ──────────────────────────────────────┐
│  ✓ Gateway healthy                                           │
│  ✓ Control Centre healthy                                    │
│  ✓ Playground preset certified (gemma-12b-gpu)               │
│  ✓ Production model certified (qwen3-7b)                     │
│  ✓ Inference image pullable                                  │
│  ✗ NVIDIA GPU available (required for gemma-12b-gpu)         │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Component specs

### CertifiedModelPicker

```python
def certified_model_picker(
    lead_id: str,
    *,
    presets: list[dict],
    models: list[dict],
    selected_preset: str,
    selected_model: str,
    recommended_preset: str,
    recommended_model: str,
    profile: str,
    lab_vram_gb: float | None,
) -> FT: ...
```

- Radio groups (native, same pattern as infrastructure stage selector)
- `★ Recommended` badge when key matches assessment
- Disabled state with `title` tooltip for VRAM-incompatible models

### ModelCardSummary

Compact card: display name, backend, VRAM, capabilities chips, license badge.

### ParityBanner

MonsterUI `AlertT.warning` when preset HF id ≠ production model; always shown when tiers differ (expected case).

---

## 5. MonsterUI mapping

| Element | Component |
|---------|-----------|
| Section container | `Card` |
| Preset/model options | `LabelRadio` in `Div.flex.flex-col.gap-2` |
| Capabilities | `UkBadge` or small `Span` chips |
| Parity note | `Alert(cls=AlertT.warning)` |
| Workbench link | `A(href=..., target="_blank")` |
| Disabled model | `LabelRadio` with `disabled=True`, `cls="opacity-50"` |

---

## 6. Step map update

| Step | Model UI |
|------|----------|
| 4 `assessment_run` | Read-only `CertifiedModelPanel` |
| 7 `branding_kit` | Full `CertifiedModelPicker` + branding form |
| 8 `deploy_lab` | Preflight checks include certified packaging |
| 14 `ship_prep` | Read-only production model recap |

---

**See also:** [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md), [UX-component-catalog-v1.md](./UX-component-catalog-v1.md)
