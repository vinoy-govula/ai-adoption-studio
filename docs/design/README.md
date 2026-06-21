# Design Pack Index — Adoption Studio Operator Wizard v1

**Status:** Draft for review  
**Parent spec:** [Deliverable Set E](../../ai-runtime-manager/docs/architecture/adoption-studio-deliverable-set-e-v1.md)

**Application form:** FastHTML + HTMX + **MonsterUI** web wizard. See [ADR-004-monsterui-web-wizard-v1.md](./ADR-004-monsterui-web-wizard-v1.md). (Supersedes [ADR-003](./ADR-003-console-application.md).)

---

## Start here

| Document | Audience | Purpose |
|----------|----------|---------|
| [EXEC-SUMMARY-operator-wizard-v1.md](./EXEC-SUMMARY-operator-wizard-v1.md) | Stakeholders | One-page overview and review ask |

---

## Suggested review order

| Order | Document | Review objective |
|-------|----------|------------------|
| **1** | [EXEC-SUMMARY-operator-wizard-v1.md](./EXEC-SUMMARY-operator-wizard-v1.md) | Problem, web wizard direction, scope, metrics |
| **2** | [ADR-004-monsterui-web-wizard-v1.md](./ADR-004-monsterui-web-wizard-v1.md) | FastHTML + MonsterUI + HTMX stack |
| **3** | [BRD-adoption-studio-operator-wizard-v1.md](./BRD-adoption-studio-operator-wizard-v1.md) | Personas, RACI, scope, KPIs |
| **4** | [PRD-operator-wizard-v1.md](./PRD-operator-wizard-v1.md) | 16 wizard steps, acceptance criteria |
| **5** | [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md) | Layout, HTMX navigation, step map |
| **6** | [UX-component-catalog-v1.md](./UX-component-catalog-v1.md) | MonsterUI components per step |
| **7** | [ARCH-adoption-studio-wizard-v1.md](./ARCH-adoption-studio-wizard-v1.md) | Layers, artifacts, integrations |
| **8** | [ADR-001](./ADR-001-wizard-orchestration-boundaries.md) · [ADR-002](./ADR-002-cursor-agent-certification.md) | Boundaries, Cursor guardrails |
| **9** | [SPEC-wizard-state-model-v1.md](./SPEC-wizard-state-model-v1.md) | workflow-state.json, jobs |
| **10** | [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md) | Routes, MonsterUI bootstrap, auth |
| **11–17** | Other SPEC-* docs | Forms, deploy, status, LLM, validation, cursor |
| **18–20** | PLAN, TEST, PIR | Delivery and quality |

---

## Architecture

| Document | Purpose |
|----------|---------|
| [ARCH-adoption-studio-wizard-v1.md](./ARCH-adoption-studio-wizard-v1.md) | Components, integrations, state machine |
| [ADR-001-wizard-orchestration-boundaries.md](./ADR-001-wizard-orchestration-boundaries.md) | Deploy/validate without boundary violations |
| [ADR-002-cursor-agent-certification.md](./ADR-002-cursor-agent-certification.md) | Cursor SDK integration and guardrails |
| [ADR-004-monsterui-web-wizard-v1.md](./ADR-004-monsterui-web-wizard-v1.md) | **Accepted** — FastHTML + MonsterUI web wizard |
| [ADR-003-console-application.md](./ADR-003-console-application.md) | Superseded — CLI/TUI (historical) |

---

## UX / interaction (web)

| Document | Purpose |
|----------|---------|
| [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md) | Step map, HTMX patterns, wireframes |
| [UX-component-catalog-v1.md](./UX-component-catalog-v1.md) | MonsterUI + HTMX components |

---

## Technical specifications

| Document | Purpose |
|----------|---------|
| [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md) | Routes, MonsterUI app bootstrap, auth |
| [SPEC-wizard-state-model-v1.md](./SPEC-wizard-state-model-v1.md) | Workflow state, artifacts, idempotency |
| [SPEC-dynamic-forms-v1.md](./SPEC-dynamic-forms-v1.md) | Question-set → MonsterUI forms |
| [SPEC-deployment-orchestration-v1.md](./SPEC-deployment-orchestration-v1.md) | Deploy adapter, async jobs, logs |
| [SPEC-live-status-aggregation-v1.md](./SPEC-live-status-aggregation-v1.md) | Health polling, status grid |
| [SPEC-validation-ui-v1.md](./SPEC-validation-ui-v1.md) | Validation trigger, report UI |
| [SPEC-llm-test-selection-v1.md](./SPEC-llm-test-selection-v1.md) | Operator capability selection |
| [SPEC-cursor-agent-bridge-v1.md](./SPEC-cursor-agent-bridge-v1.md) | Certification, troubleshoot, PIR |

---

## Implementation & quality

| Document | Purpose |
|----------|---------|
| [PLAN-implementation-phases-v1.md](./PLAN-implementation-phases-v1.md) | Phased delivery plan |
| [TEST-plan-wizard-v1.md](./TEST-plan-wizard-v1.md) | Test strategy and golden path |
| [PIR-template-v1.md](./PIR-template-v1.md) | Platform Improvement Record template |

---

## External references

- [Operator guide](../README.md)
- [MonsterUI](https://monsterui.answer.ai/)
- [Control Centre UI stack](../../ai-control-centre/.cursor/rules/server-rendered-ui.mdc) — FastHTML + HTMX + Tailwind (Studio adds MonsterUI)

---

After approval, request the **implementation prompt** to build in `ai-adoption-studio`.
