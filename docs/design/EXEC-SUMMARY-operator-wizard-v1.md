# Executive Summary — Adoption Studio Operator Wizard v1

**Status:** Draft for review  
**Parent spec:** [Deliverable Set E](../../ai-runtime-manager/docs/architecture/adoption-studio-deliverable-set-e-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## Problem

The current Adoption Studio is a minimal internal prototype: static forms, hardcoded assessment fields, manual checkpoint buttons, and no deploy/validate/status workflow. Operators cannot run the full **EOI → Assessment → Playground → Validate → Ship** lifecycle from a single guided experience.

## Proposed solution

Replace the prototype with a **browser-based operator wizard** using **FastHTML + HTMX + MonsterUI** that:

1. **Guides** the operator step-by-step with back/forward navigation and checkpoint gates (cp0–cp4).
2. **Generates forms dynamically** from question-set JSON via MonsterUI form components.
3. **Orchestrates** playground kit generation, lab deployment, and validation via `ai-delivery-validator` and Runtime Manager.
4. **Surfaces live stack health** with HTMX polling (Runtime, Gateway, Control Centre, SDK).
5. **Lets the operator choose a capability** to test the deployment (Platform SDK, capability-first).
6. **Integrates Cursor Agent** for certification, troubleshooting, and PIR feedback.

**Application form:** [ADR-004 — FastHTML + MonsterUI web wizard](./ADR-004-monsterui-web-wizard-v1.md). Supersedes ADR-003 (CLI/TUI).

## What stays where

| Concern | Owner repo |
|---------|------------|
| Operator wizard UI, workflow state | `ai-adoption-studio` |
| JSON schemas, rule engine, validation harness | `ai-runtime-manager` |
| Lab deploy orchestration | `ai-delivery-validator` |
| Inference, routing, governance | `ai-gateway` |
| Ops console, keys, inventory | `ai-control-centre` |
| Application consumption in tests | `ai-platform-sdk` |

## Success metrics

| Metric | Target |
|--------|--------|
| First deployment | < 5 business days |
| Operator time per lead (lab path) | < 2 hours hands-on |
| Validation automation coverage | 100% of manifest automated checks |
| Failed deploy diagnosis | < 15 minutes with Cursor assist |

## Review ask

1. **Web stack** — [ADR-004](./ADR-004-monsterui-web-wizard-v1.md): FastHTML + MonsterUI + HTMX.
2. Wizard steps — [PRD](./PRD-operator-wizard-v1.md), [UX flow](./UX-wizard-flow-v1.md).
3. Boundaries — [ADR-001](./ADR-001-wizard-orchestration-boundaries.md).
4. LLM test selection — [SPEC-llm-test-selection-v1.md](./SPEC-llm-test-selection-v1.md).
5. Cursor guardrails — [ADR-002](./ADR-002-cursor-agent-certification.md).

After approval, request the **implementation prompt**.

---

**Next:** [README.md](./README.md)
