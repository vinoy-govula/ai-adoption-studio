# PLAN — Implementation Phases v1

**Status:** Draft for review  
**Parent spec:** [EXEC-SUMMARY-operator-wizard-v1.md](./EXEC-SUMMARY-operator-wizard-v1.md)  
**Application form:** FastHTML + HTMX + MonsterUI — [ADR-004](./ADR-004-monsterui-web-wizard-v1.md)

---

## Phase 0 — Foundation (Week 1)

**Goal:** MonsterUI layout, wizard shell, state model, auth.

| Task | Module |
|------|--------|
| Add `monsterui` to pyproject.toml | `pyproject.toml` |
| Refactor `layouts/base.py` — `Theme.slate.headers()` | `layouts/base.py` |
| WorkflowState + WizardService | `models/`, `services/wizard_service.py` |
| Wizard shell + Stepper component | `pages/wizard.py`, `components/stepper.py` |
| Auth middleware | `middleware/auth.py` |

**Exit:** Navigate wizard steps; MonsterUI sidebar + card content area.

---

## Phase 1 — Dynamic forms & assessment (Week 2)

**Goal:** MonsterUI forms from question sets; assessment path.

| Task | Module |
|------|--------|
| QuestionSetLoader + MonsterUI DynamicForm | `services/`, `components/` |
| Wizard steps 1–6 (EOI through cp2) | `pages/wizard_steps/` |
| RecommendationCard with `render_md` for narrative | `components/` |

**Exit:** Golden path EOI → assessment report with full question fields.

---

## Phase 2 — Playground kit & deploy (Week 3)

**Goal:** Kit generation and lab deploy from UI.

| Task | Module |
|------|--------|
| DeploymentOrchestrator adapter | `adapters/delivery_validator.py` |
| Job runner + DeployLogViewer (HTMX poll) | `services/`, `components/` |
| BrandingForm + deploy step | wizard steps 7–8 |

**Exit:** Operator generates manifest and deploys from wizard.

---

## Phase 3 — Status, LLM selection, validation (Week 4)

**Goal:** StatusGrid HTMX polling, CapabilityPicker, validation UI.

| Task | Repo |
|------|------|
| StatusAggregator + StatusGrid | Studio |
| CapabilityPicker + smoke HTMX endpoint | Studio |
| ValidationResults + manual checklist | Studio |
| `STUDIO_VALIDATION_CAPABILITY` in SDK checks | RM `playground.py` |

**Exit:** Operator selects capability, runs validation, views deployment-report.

---

## Phase 4 — Cursor assist & polish (Week 5)

**Goal:** CursorAssist modal, cp3/cp4, export, cleanup.

| Task | Module |
|------|--------|
| CursorAgentBridge + modal panel | `adapters/`, `components/` |
| Ship prep, cp4, export in wizard | wizard steps 14–16 |
| Remove legacy `/leads/{id}` hardcoded UI | cleanup |
| Accessibility pass | all components |

**Exit:** Full golden path with Cursor certify.

---

## Cross-repo tasks

| ID | Repo | Task | Phase |
|----|------|------|-------|
| X-1 | ai-runtime-manager | Env-based capability in validation | 3 |
| X-2 | ai-runtime-manager | manifest `validation.test_capability` schema | 3 |
| X-3 | ai-delivery-validator | Forward capability env | 3 |

---

## Risks

| Risk | Mitigation |
|------|------------|
| MonsterUI API changes | Pin version; follow llms.txt |
| HTMX polling load | Tune intervals; stop poll when step inactive |
| Windows subprocess deploy | Test PowerShell; document WSL2 |

---

**See also:** [TEST-plan-wizard-v1.md](./TEST-plan-wizard-v1.md)
