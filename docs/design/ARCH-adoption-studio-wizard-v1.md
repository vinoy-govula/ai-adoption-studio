# Architecture — Adoption Studio Operator Wizard v1

**Status:** Draft for review  
**Parent spec:** [Deliverable Set E](../../ai-runtime-manager/docs/architecture/adoption-studio-deliverable-set-e-v1.md)  
**Application form:** FastHTML + HTMX + MonsterUI — [ADR-004](./ADR-004-monsterui-web-wizard-v1.md)

---

## 1. System context

```text
                    ┌─────────────────────────────────────┐
                    │         ai-adoption-studio          │
                    │  FastHTML + MonsterUI + HTMX        │
                    │  Wizard UI │ BFF │ Job runner       │
                    └───────────┬─────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ ai-runtime-   │    │ ai-delivery-     │    │ Cursor SDK      │
│ manager       │    │ validator        │    │ certify/troubles│
└───────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
              Lab stack: Runtime → Gateway → Control Centre
              Tests via ai-platform-sdk (capability)
```

---

## 2. Layered architecture (Studio)

| Layer | Responsibility | Modules |
|-------|----------------|---------|
| **Pages** | MonsterUI wizard views | `pages/wizard.py`, `pages/inbox.py`, `pages/wizard_steps/` |
| **Components** | HTMX fragments | `components/*.py` |
| **Layouts** | Theme, sidebar | `layouts/base.py` |
| **Services** | Workflow orchestration | `services/wizard_service.py`, `assessment_service.py` |
| **Adapters** | External integration | `adapters/delivery_validator.py`, `gateway_client.py`, `cursor_agent.py` |
| **Store** | Artifacts + state | `services/store.py`, `workflow-state.json` |

---

## 3. Artifact model

Per lead under `STUDIO_DATA_ROOT/{lead_id}/`:

| File | Schema |
|------|--------|
| `eoi-intent.json` | eoi-intent |
| `internal-responses.json` | question-set keys |
| `assessment-report.json` | assessment-report |
| `playground-kit.manifest.json` | playground-kit.manifest |
| `deployment-report.json` | deployment-report |
| `workflow-state.json` | Studio-defined |
| `branding.json` | Studio-defined |
| `jobs/{job_id}.json` | Studio-defined |

---

## 4. Integration matrix

Same as prior ARCH — Studio orchestrates via delivery-validator subprocess, polls Gateway/CC for status, SDK for smoke tests. See [ADR-001](./ADR-001-wizard-orchestration-boundaries.md).

---

## 5. BFF + HTMX

JSON/HTML endpoints for polling: status, capabilities, jobs, smoke-test, cursor. Secrets server-side only.

---

## 6. Async jobs

Deploy/validate/Cursor runs as background tasks; HTMX polls every 2s; optional SSE in Phase 2.

---

## 7. Decision log

| Decision | Rationale |
|----------|-----------|
| FastHTML + MonsterUI | Platform alignment + richer UX (ADR-004) |
| HTMX polling | Server-rendered live status without SPA |
| Subprocess delivery-validator | Boundary-safe deploy/validate |

---

## 8. Implementation checklist

- [ ] MonsterUI in `pyproject.toml`
- [ ] `layouts/base.py` theme refactor
- [ ] `services/wizard_service.py`
- [ ] `adapters/` package

---

**See also:** [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md)
