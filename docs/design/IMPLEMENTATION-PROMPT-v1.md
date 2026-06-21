# Implementation Prompt — Adoption Studio Operator Wizard v1

Copy everything below the line into Cursor Agent mode with the `ai-adoption-studio` repo open (multi-root workspace with sibling `ai-runtime-manager`, `ai-delivery-validator`, `deployment-catalog` recommended).

---

## PROMPT START

You are implementing the **Adoption Studio Operator Wizard** in `ai-adoption-studio`. The design pack is **approved**. Follow it exactly.

### Authoritative documents (read first)

All under `ai-adoption-studio/docs/design/`:

| Priority | Document |
|----------|----------|
| Stack | [ADR-004-monsterui-web-wizard-v1.md](./ADR-004-monsterui-web-wizard-v1.md) |
| Plan | [PLAN-implementation-phases-v1.md](./PLAN-implementation-phases-v1.md) |
| Routes | [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md) |
| State | [SPEC-wizard-state-model-v1.md](./SPEC-wizard-state-model-v1.md) |
| UX | [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md), [UX-component-catalog-v1.md](./UX-component-catalog-v1.md) |
| Forms | [SPEC-dynamic-forms-v1.md](./SPEC-dynamic-forms-v1.md) |
| Deploy | [SPEC-deployment-orchestration-v1.md](./SPEC-deployment-orchestration-v1.md), [ADR-001-wizard-orchestration-boundaries.md](./ADR-001-wizard-orchestration-boundaries.md) |
| Status | [SPEC-live-status-aggregation-v1.md](./SPEC-live-status-aggregation-v1.md) |
| LLM test | [SPEC-llm-test-selection-v1.md](./SPEC-llm-test-selection-v1.md) |
| Validate | [SPEC-validation-ui-v1.md](./SPEC-validation-ui-v1.md) |
| Cursor | [SPEC-cursor-agent-bridge-v1.md](./SPEC-cursor-agent-bridge-v1.md), [ADR-002-cursor-agent-certification.md](./ADR-002-cursor-agent-certification.md) |
| Tests | [TEST-plan-wizard-v1.md](./TEST-plan-wizard-v1.md) |
| Product | [PRD-operator-wizard-v1.md](./PRD-operator-wizard-v1.md) |

Question sets: `docs/eoi-question-set-v1.json`, `docs/assessment-question-set-internal-v1.json`  
Schemas (read-only): `../ai-runtime-manager/docs/schemas/`  
Existing services to extend: `services/assessment_service.py`, `services/store.py`

### Technology stack (non-negotiable)

- **FastHTML** — app, routes, HTMX
- **MonsterUI** — `Theme.slate.headers()`, `Card`, `LabelInput`, `LabelSelect`, `render_md()`, etc.
- **HTMX** — step navigation, polling (status 10s, jobs 2s)
- **Pydantic v2** — workflow state, settings, job records
- **Python 3.13**, type hints on all public functions

**Do NOT use:** Textual, Typer wizard, Streamlit, Gradio, SPA/React, raw Tailwind CDN (replace with MonsterUI theme headers).

### Platform boundaries (non-negotiable)

- Studio **orchestrates** deploy/validate via `ai-delivery-validator` subprocess — never runs `docker compose` directly ([ADR-001](./ADR-001-wizard-orchestration-boundaries.md)).
- Inference tests use **`ai_platform.AIClient.chat(capability=...)`** — capability-first, not raw model IDs.
- Do not duplicate RM validation logic — call existing CLIs/adapters.
- Keep secrets server-side (`STUDIO_PLATFORM_API_KEY`, `STUDIO_CURSOR_API_KEY`).

### Current codebase (replace incrementally)

Prototype to refactor:

- `src/ai_adoption_studio/main.py` — monolithic routes, hardcoded assessment
- `src/ai_adoption_studio/pages/studio.py` — bland forms
- `src/ai_adoption_studio/layouts/base.py` — CDN Tailwind → MonsterUI

Preserve:

- `POST /api/v1/eoi` (`api/eoi.py`)
- `services/assessment_service.py` orchestration (extend, don't rewrite rule engine)
- File-backed `LeadStore` / `ArtifactStore`

### Target module layout

```text
src/ai_adoption_studio/
  main.py                    # wire app, register routes
  config.py                  # extend Settings (gateway URLs, API keys, paths)
  layouts/base.py            # MonsterUI page_layout + sidebar
  middleware/auth.py         # STUDIO_INTERNAL_API_KEY on /wizard/* and /api/leads/*
  models/
    workflow_state.py
    job_record.py
  services/
    wizard_service.py
    question_set_loader.py
    form_validator.py
    job_runner.py
    status_aggregator.py
    smoke_test_service.py
    validation_ui_service.py
    certification_service.py   # Phase 4
  adapters/
    delivery_validator.py
    gateway_client.py
    runtime_manager_client.py
    control_centre_client.py
    cursor_agent.py            # Phase 4
  components/                  # MonsterUI + HTMX fragments
  pages/
    inbox.py
    wizard.py
    wizard_steps/              # one partial per step
  routes/
    api_leads.py
    api_jobs.py
    api_cursor.py              # Phase 4
  api/eoi.py                   # keep public EOI
```

### Wizard steps (16 + inbox)

Implement per [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md):

`inbox` → `eoi_review` → `qualify` → `assessment_form` → `assessment_run` → `narrative` → `cp2_approve` → `branding_kit` → `deploy_lab` → `live_status` → `llm_test_select` → `validate` → `manual_cc` → `cp3_approve` → `ship_prep` → `cp4_approve` → `export`

- Back/Next/Save draft on every step
- Step unlock rules in [SPEC-wizard-state-model-v1.md](./SPEC-wizard-state-model-v1.md)
- Persist `workflow-state.json` per lead

### Implementation order — execute ALL phases in one session if possible

#### Phase 0 — Foundation

1. `uv sync` with `monsterui` in pyproject.toml
2. Refactor `layouts/base.py` to MonsterUI `Theme.slate.headers(highlightjs=True)`
3. Implement `WorkflowState` + `WizardService`
4. Wizard shell: stepper sidebar + `#step-content` HTMX target
5. Auth middleware on operator routes
6. Inbox page with MonsterUI table; `/wizard/{lead_id}` entry

**Exit test:** Navigate empty wizard steps; stepper locks/unlocks correctly.

#### Phase 1 — Dynamic forms & assessment

1. `QuestionSetLoader` + `FormValidator`
2. MonsterUI `DynamicForm` / `QuestionField` from JSON question sets
3. Wire steps 1–6: EOI review, qualify, assessment form/run, narrative (`render_md`), cp2
4. `RecommendationCard` with rule_trace, confidence alerts
5. Remove hardcoded fields from old `main.py` / `studio.py`
6. Redirect `/leads/{id}` → `/wizard/{id}`

**Exit test:** Full assessment from dynamic internal form → `assessment-report.json`.

#### Phase 2 — Kit & deploy

1. `DeploymentOrchestrator` adapter (subprocess to `ai-delivery-validator`)
2. `JobRunner` + `DeployLogViewer` (HTMX poll logs)
3. BrandingForm + kit generation step
4. Deploy step with prerequisites checklist (MonsterUI)
5. Extend `config.py`: `delivery_validator_root`, gateway/RM/CC URLs, `platform_api_key`

**Exit test:** Generate manifest + start deploy job from UI (mock subprocess in tests).

#### Phase 3 — Status, LLM selection, validation

1. `StatusAggregator` + `StatusGrid` (HTMX poll `/api/leads/{id}/status`)
2. `GatewayClient.list_capabilities()` + `CapabilityPicker`
3. `POST /api/leads/{id}/smoke-test` via SDK with selected capability
4. Validation step + `ValidationResults` + `ManualChecklist`
5. **Cross-repo (minimal):** In `ai-runtime-manager/src/ai_runtime_manager/validation/playground.py`, read `STUDIO_VALIDATION_CAPABILITY` env for SDK smoke checks if not already present

**Exit test:** Capability picker, smoke test, validation job trigger, deployment-report display.

#### Phase 4 — Cursor assist & polish

1. `CursorAgentBridge` + `CursorAssistPanel` modal (certify/troubleshoot/PIR)
2. Redaction utility before agent calls
3. Steps cp3, cp4, ship_prep, export in wizard
4. Delete or gut legacy `pages/studio.py` if fully replaced
5. Tests per [TEST-plan-wizard-v1.md](./TEST-plan-wizard-v1.md)

**Exit test:** Golden path test with mocked adapters; Cursor certify returns verdict JSON.

### HTMX patterns (required)

| Use case | Pattern |
|----------|---------|
| Step submit | `hx-post` → `#step-content` |
| Stepper update | `hx-swap="outerHTML"` on sidebar |
| Live status | `hx-trigger="every 10s"` on StatusGrid |
| Job progress | `hx-trigger="every 2s"` on DeployLogViewer / JobProgress |
| Stop polling | Remove trigger when navigating away from step |

### Config env vars (add to config.py + README)

| Variable | Purpose |
|----------|---------|
| `STUDIO_DATA_ROOT` | Artifact root |
| `STUDIO_INTERNAL_API_KEY` | Operator auth |
| `STUDIO_PLATFORM_API_KEY` | Gateway/SDK tests |
| `STUDIO_GATEWAY_BASE_URL` | Default `http://localhost:8000` |
| `STUDIO_RUNTIME_MANAGER_BASE_URL` | Default `http://localhost:8001` |
| `STUDIO_CONTROL_CENTRE_BASE_URL` | Default `http://localhost:8002` |
| `STUDIO_DELIVERY_VALIDATOR_ROOT` | Sibling path |
| `STUDIO_CURSOR_API_KEY` | Phase 4 |
| `STUDIO_CURSOR_WORKSPACE_ROOT` | Parent AI Adoption folder |
| `LOCAL_LLM_BASE_URL` | Narrative generation (existing) |

### Testing requirements

- `tests/test_wizard_service.py` — step unlock, back navigation, invalidation
- `tests/test_dynamic_forms.py` — all question types validate
- `tests/test_golden_path.py` — mocked adapters, full wizard flow
- Update existing `tests/test_studio.py` for new routes
- Mock subprocess for deploy/validate; mock `AIClient` for smoke
- Mark live stack tests `@pytest.mark.live_stack`

Run: `uv run pytest -v`

### Code quality rules

- Match existing repo style (snake_case, async I/O for httpx)
- Pages thin; logic in services/adapters
- No secrets in HTML/JS
- No git commits unless user asks
- Minimal scope — no unrelated refactors

### Deliverables checklist

When done, report:

- [ ] Files created/modified list
- [ ] Phase 0–4 status
- [ ] Cross-repo changes (RM playground.py if any)
- [ ] How to run: `uv run uvicorn ai_adoption_studio.main:app --reload --port 8010`
- [ ] Known gaps / follow-ups

Start by reading the design docs listed above, then implement Phase 0 → Phase 4 sequentially. Run tests after each phase.

## PROMPT END
