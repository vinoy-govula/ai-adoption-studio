# BRD — Adoption Studio Operator Wizard v1

**Status:** Draft for review  
**Parent spec:** [Deliverable Set E](../../ai-runtime-manager/docs/architecture/adoption-studio-deliverable-set-e-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. Business context

Deliverable Set E defines an internal **Adoption Studio** workflow that accelerates private AI time-to-adoption:

```text
EOI → Assessment → Playground → Validate → Ship
```

Revenue streams tied to this flow: AI Readiness Assessment, Platform Licensing, Deployment Services, Knowledge Onboarding, Training & Adoption, Custom SOW.

The operator wizard is the **primary internal product surface** for running this lifecycle with minimal manual coordination across CLI tools, spreadsheets, and ad-hoc checklists.

---

## 2. Problem statement

| Pain | Impact |
|------|--------|
| Bland, minimal prototype with hardcoded forms | Data quality gaps; rule engine inputs incomplete |
| No guided wizard workflow | Operators skip checkpoints; audit trail weak |
| Deploy/validate without UI orchestration | High skill barrier; slow time-to-playground |
| No unified stack visibility | Long MTTR on failed lab deploys |
| No structured certification | Subjective go/no-go decisions |

---

## 3. Personas

| Persona | Role | Primary wizard steps |
|---------|------|----------------------|
| **Sales operator** | Qualifies leads, triggers cp1 | EOI review, Qualify |
| **Adoption engineer** | Runs assessment, deploys lab, validates | Assessment through cp3 |
| **Delivery lead** | Approves handover | cp4, export |
| **Architect reviewer** | Mandatory review when confidence < 85% or hard gates | Recommendation review |
| **Client approver** | External; approves pack (cp2) | Recommendation review (email capture) |

---

## 4. Business outcomes

1. **First client playground live in < 5 business days** from EOI (Deliverable Set E target).
2. **Reduce operator hands-on time** per lead to under 2 hours for standard lab path.
3. **100% checkpoint traceability** — every cp0–cp4 recorded with actor and timestamp in artifacts.
4. **Repeatable validation** — same automated suite, operator-selected test capability/model path.
5. **Continuous platform improvement** — failed runs feed PIRs back to RM/Gateway/docs.

---

## 5. Scope

### In scope (v1 wizard)

- **FastHTML + HTMX + MonsterUI web wizard** with back/forward navigation per lead
- Dynamic EOI and internal assessment forms from question-set JSON
- Rule-engine assessment, narrative generation, cp1/cp2 UX
- Playground kit generation and lab deploy orchestration (via delivery-validator)
- Live status dashboard (Runtime, Gateway, Control Centre, SDK)
- Operator **LLM/capability selection** for deployment validation tests
- Automated validation UI + manual Control Centre checklist
- Cursor Agent certification and troubleshoot panel
- Pipeline CSV export (existing RM capability, wizard-triggered)

### Out of scope (v1)

- Public marketing website (optional `studio serve-eoi` for HTTP intake only; no operator web UI)
- Production deploy to client hardware (Phase 4 ship orchestration is checkpoint + export only in v1)
- Accelerator business logic (Knowledge Assistant plug-in deferred)
- Direct Gateway admin (keys via Control Centre deep links)
- Auto-merge of agent-suggested code changes

---

## 6. Checkpoint RACI

| Checkpoint | Accountable | Responsible | Consulted | Informed |
|------------|-------------|-------------|-----------|----------|
| cp0_eoi_submitted | Sales | System (EOI API) | — | Adoption engineer |
| cp1_lead_qualified | Sales manager | Sales operator | Adoption engineer | Delivery |
| cp2_assessment_approved | Client sponsor | Sales operator | Architect (if review) | Delivery |
| cp3_deploy_test_approved | Delivery lead | Adoption engineer | Architect | Client |
| cp4_ship_approved | Delivery lead | Delivery operator | Adoption engineer | Client |

---

## 7. Success metrics

| KPI | Baseline | Target |
|-----|----------|--------|
| Time EOI → lab URL | Days (manual) | < 5 business days |
| Assessment form completion rate | ~30% fields (hardcoded) | 100% required fields |
| Validation run without wizard UI | 0% | 100% |
| Failed check → resolution time | Hours | < 15 min with Cursor assist |
| Architect review trigger accuracy | N/A | Matches rule-engine spec |

---

## 8. Decision log

| Decision | Rationale | Rejected alternative |
|----------|-----------|---------------------|
| FastHTML + MonsterUI (ADR-004) | Rich web wizard; aligns with Control Centre stack | Textual TUI (ADR-003, superseded) |
| Orchestrate deploy via delivery-validator | Boundary-safe; existing CLI | Studio runs docker compose directly |
| Capability-first LLM test selection | Platform principle; SDK mandatory | Raw model picker bypassing Gateway |
| Cursor SDK for certify/troubleshoot | Skills+rules injection; audit trail | Ad-hoc OpenAI calls from Studio |

---

## 9. Open questions

None blocking — recommendations made in linked specs. Confirm LLM selection defaults in [SPEC-llm-test-selection-v1.md](./SPEC-llm-test-selection-v1.md).

---

## 10. Implementation checklist

- [ ] Stakeholder sign-off on personas and RACI
- [ ] Confirm v1 out-of-scope list
- [ ] Approve success metrics

---

**See also:** [PRD-operator-wizard-v1.md](./PRD-operator-wizard-v1.md)
