# Adoption Studio — Operator Guide

Internal EOI intake, assessment workflow, and pipeline export for the AI Adoption Factory.

Application code lives in this repository. Rule engine, JSON schemas, playground validation, and delivery specs live in [ai-runtime-manager](../ai-runtime-manager).

**Operator experience:** Console application (`studio` CLI + Textual TUI) — see [design/ADR-003-console-application.md](./design/ADR-003-console-application.md).

**Operator wizard design pack:** [design/README.md](./design/README.md) — FastHTML + MonsterUI + HTMX ([ADR-004](./design/ADR-004-monsterui-web-wizard-v1.md))

---

## Workflow

1. Collect EOI via public questionnaire → `eoi-intent.json`
2. Run internal assessment → rule engine → `assessment-report.json`
3. Generate LLM narrative → `assessment-report.md` (advisory only)
4. After cp2 approval, create `playground-kit.manifest.json` and deploy lab stack
5. After cp3 approval, run validation (see [validation-suite-spec-v1.md](../../ai-runtime-manager/docs/adoption-studio/validation-suite-spec-v1.md))
6. Complete manual Control Centre checklist; export CSV for sales pipeline

---

## Question sets

| File | Visibility |
|------|------------|
| [eoi-question-set-v1.json](./eoi-question-set-v1.json) | Public website |
| [assessment-question-set-internal-v1.json](./assessment-question-set-internal-v1.json) | Internal only |

Question IDs in these files map to `responses` keys in [eoi-intent.schema.json](../../ai-runtime-manager/docs/schemas/eoi-intent.schema.json).

---

## JSON schemas (canonical — ai-runtime-manager)

| Schema | Example |
|--------|---------|
| [eoi-intent.schema.json](../../ai-runtime-manager/docs/schemas/eoi-intent.schema.json) | [eoi-intent.example.json](../../ai-runtime-manager/docs/schemas/examples/eoi-intent.example.json) |
| [assessment-report.schema.json](../../ai-runtime-manager/docs/schemas/assessment-report.schema.json) | [assessment-report.example.json](../../ai-runtime-manager/docs/schemas/examples/assessment-report.example.json) |
| [playground-kit.manifest.schema.json](../../ai-runtime-manager/docs/schemas/playground-kit.manifest.schema.json) | [playground-kit.manifest.example.json](../../ai-runtime-manager/docs/schemas/examples/playground-kit.manifest.example.json) |
| [deployment-report.schema.json](../../ai-runtime-manager/docs/schemas/deployment-report.schema.json) | [deployment-report.example.json](../../ai-runtime-manager/docs/schemas/examples/deployment-report.example.json) |

---

## Architecture

| Document | Description |
|----------|-------------|
| [adoption-studio-deliverable-set-e-v1.md](../../ai-runtime-manager/docs/architecture/adoption-studio-deliverable-set-e-v1.md) | Master Deliverable Set E |
| [adoption-studio-playground-v1.md](../../ai-runtime-manager/docs/architecture/adoption-studio-playground-v1.md) | Playground kit architecture |
| [adoption-studio README](../../ai-runtime-manager/docs/adoption-studio/README.md) | Rule engine, validation, and CLI index |

---

## Checkpoints

| ID | Description |
|----|-------------|
| cp0_eoi_submitted | Website EOI |
| cp1_lead_qualified | Sales qualification |
| cp2_assessment_approved | Client sign-off on pack |
| cp3_deploy_test_approved | Lab validation approved |
| cp4_ship_approved | Client handover approved |
