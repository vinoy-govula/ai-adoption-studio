# SPEC — Certified Model Picker v1

**Status:** Accepted  
**Parent spec:** [PRD-operator-wizard-v1.md](./PRD-operator-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`  
**Catalog authority:** [ai-open-llm-workbench SPEC](../../../ai-open-llm-workbench/docs/SPEC-workbench-rm-promotion-v1.md) · [RM promotion API](../../../ai-runtime-manager/docs/adoption-studio/SPEC-workbench-promotion-api-v1.md)

---

## 1. Purpose

Adoption Studio operators **select certified validation presets and production models only** when configuring playground kits and reviewing assessment recommendations. Studio does not browse Hugging Face, build Docker images, or manage weights — that is Open LLM Workbench.

---

## 2. Principles

| Rule | Enforcement |
|------|-------------|
| Certified only | All catalog calls use `status=certified` |
| Read-only cards | Full Model Card from RM; no inline editing |
| Profile-aware filtering | Hide models/presets incompatible with recommended profile or lab GPU |
| Parity visibility | Always show lab preset vs production model difference |
| Workbench link-out | "Manage models" links to Workbench (platform engineers) |

---

## 3. Wizard integration

### Step 4 — Assessment run (read-only preview)

After rule engine runs, show **Recommended models** panel:

- Default validation preset from assessment `playground_preset_key`
- Default production model from assessment `production_model`
- Read-only cards: display name, VRAM, capabilities, license
- No picker yet — informational only

### Step 7 — Playground kit (primary picker)

Operator confirms or overrides certified selections before manifest generation.

**Persisted to:**

- `workflow-state.json` → `branding.playground_preset_key`, `branding.production_model`
- `playground-kit.manifest.json` → `deployment.playground_preset`, `deployment.production_target`

**Gate:** Generate manifest disabled until both preset and production model selected.

### Step 14 — Ship prep (read-only recap)

Display final certified production model + parity note from manifest. No override (change requires returning to step 7).

---

## 4. Data sources (Runtime Manager)

```http
GET {RUNTIME_MANAGER_BASE_URL}/api/v1/presets?status=certified
GET {RUNTIME_MANAGER_BASE_URL}/api/v1/models?status=certified&profile={profile}
GET {RUNTIME_MANAGER_BASE_URL}/api/v1/catalog/recommendations?profile={profile}&has_gpu={bool}&vram_gb={n}
GET {RUNTIME_MANAGER_BASE_URL}/api/v1/presets/{key}/card
GET {RUNTIME_MANAGER_BASE_URL}/api/v1/models/{key}/card
```

Adapter: `adapters/runtime_manager_client.py` (extend existing or new).

Default selections from assessment recommendation when keys exist in certified catalog; otherwise first compatible certified entry.

---

## 5. Persistence

### workflow-state.json

```json
"branding": {
  "playground_preset_key": "gemma-12b-gpu",
  "production_model": "qwen3-7b",
  "model_selection_source": "recommended|operator"
}
```

### playground-kit.manifest.json

Unchanged structure; `deployment.playground_preset` and `deployment.production_target` populated from certified catalog + Model Card metadata at generate time.

---

## 6. Components

| Component | Module | Purpose |
|-----------|--------|---------|
| `CertifiedModelPanel` | `components/certified_model_panel.py` | Step 4 read-only preview |
| `CertifiedModelPicker` | `components/certified_model_picker.py` | Step 7 preset + production selectors |
| `ModelCardSummary` | `components/model_card_summary.py` | Compact card (VRAM, license, capabilities) |
| `ParityBanner` | `components/parity_banner.py` | Lab vs production note |

---

## 7. Deploy preflight (step 8 enhancement)

Before starting deploy job, validate manifest references certified catalog entries with pullable images:

| Check | Failure message |
|-------|-----------------|
| Preset key exists and `certified` | "Playground preset not certified" |
| Production model certified | "Production model not certified" |
| Image digest resolvable | "Inference image not pullable: {image}" |
| GPU required but unavailable | "Preset requires {n} GB VRAM" |

Surface in deploy prerequisites card and embedded terminal on failure.

---

## 8. Error states

| Error | UX |
|-------|-----|
| RM unreachable | Alert: configure `STUDIO_RUNTIME_MANAGER_BASE_URL` |
| No certified presets | Alert + link to Workbench |
| No certified models for profile | Alert: filter relaxed or contact platform team |
| Selected key deprecated since manifest | Warning on deploy step |

---

## 9. Cross-repo dependencies

| Repo | Change |
|------|--------|
| `ai-runtime-manager` | Presets API, recommendations API, Model Card detail, compose from packaging |
| `ai-open-llm-workbench` | Promote seed presets/models |
| `ai-adoption-studio` | Picker components, RM client, workflow persistence, step 7/4/14 render |

---

## 10. Implementation checklist

- [ ] `RuntimeManagerClient.list_presets()`, `list_models()`, `get_recommendations()`
- [ ] `components/certified_model_picker.py`
- [ ] Step 7 render integration in `pages/wizard_steps/render.py`
- [ ] Step 4 recommendation panel extension
- [ ] Manifest generation passes selected keys to RM kit builder
- [ ] Deploy preflight checks
- [ ] Tests: certified-only filter, profile compatibility, parity banner

---

**See also:** [UX-certified-model-picker-v1.md](./UX-certified-model-picker-v1.md)
