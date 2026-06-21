# PRD — Operator Wizard v1

**Status:** Draft for review  
**Parent spec:** [BRD-adoption-studio-operator-wizard-v1.md](./BRD-adoption-studio-operator-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. Product vision

A single lead-centric **web wizard** (FastHTML + HTMX + MonsterUI) that spoon-feeds each Deliverable Set E phase, supports non-linear review via Back/Next, and automates deploy/validate/status monitoring — including operator-chosen LLM test paths and Cursor-assisted certification.

Entry: `studio wizard {lead_id}` · Inbox: `studio leads list`

---

## 2. Wizard steps (user stories)

### Step 0 — Leads inbox

**As** an adoption engineer, **I want** a searchable leads inbox **so that** I can resume any lead's wizard.

**Acceptance criteria:**
- List shows org, industry, pipeline status, submitted date, wizard progress %
- Click opens wizard at last completed step + 1 (or last step if complete)
- Filter by status: new, qualified, assessment approved, deploying, validating, shipped

---

### Step 1 — EOI review (cp0)

**As** a sales operator, **I want** to review the full EOI **so that** I confirm data before qualification.

**Acceptance criteria:**
- Render all responses from `eoi-intent.json` with labels from question set
- Show consent flags
- Display schema validation errors if any
- cp0 auto-recorded on submission (API or form)

---

### Step 2 — Qualify (cp1)

**As** a sales operator, **I want** a one-click qualify action with confirmation **so that** cp1 is auditable.

**Acceptance criteria:**
- Confirm dialog with lead summary
- Sets `pipeline_status=qualified`, records cp1 in assessment report when exists
- Blocks if required EOI fields missing

---

### Step 3 — Internal assessment (dynamic form)

**As** an adoption engineer, **I want** the internal questionnaire rendered from JSON **so that** all rule-engine inputs are captured.

**Acceptance criteria:**
- Form generated from `assessment-question-set-internal-v1.json`
- Grouped by dimension (strategy, data, governance, infrastructure, change_readiness)
- Save draft without running assessment
- Inline validation (required, min/max, option enums)

---

### Step 4 — Run assessment & preview

**As** an adoption engineer, **I want** to run the rule engine and preview results **so that** I understand pack recommendation before narrative.

**Acceptance criteria:**
- Calls `build_assessment_report()` via existing service
- Shows recommendation, confidence, hard gates, `rule_trace`
- Flags architect review when confidence < 85% or hard gate fired
- Back preserves edited internal responses

---

### Step 5 — Narrative

**As** an adoption engineer, **I want** to generate/regenerate LLM narrative **so that** the client-facing summary exists.

**Acceptance criteria:**
- Toggle template-only vs LLM (`LOCAL_LLM_BASE_URL`)
- Show narrative preview in terminal (Rich markdown)
- Narrative does not alter recommendation (display disclaimer)

---

### Step 6 — cp2 approval

**As** a sales operator, **I want** to record client approval **so that** playground work can begin.

**Acceptance criteria:**
- Requires assessment report exists
- Captures approver email, optional notes
- Sets status `approved_for_deployment`
- Blocks if architect review mandatory and not acknowledged

---

### Step 7 — Branding & kit config

**As** an adoption engineer, **I want** to configure branding and generate playground manifest **so that** lab deploy has canonical config.

**Acceptance criteria:**
- Form: logo URL/path, welcome message, demo prompts, public URL slug, TTL
- Preview `playground-kit.manifest.json` against schema
- Generate via RM kit builder / `delivery-generate-kit`
- Save manifest to lead artifact dir

---

### Step 8 — Deploy lab

**As** an adoption engineer, **I want** to deploy the stack from the wizard UI **so that** I don't run delivery CLI manually.

**Acceptance criteria:**
- Requires cp2 approved
- Shows env prerequisites checklist (platform stack, API key)
- Triggers deploy job; streams logs in LogPanel
- Updates manifest status: `deploying` → `active` or `failed`
- On failure: link to Cursor troubleshoot panel

---

### Step 9 — Live status

**As** an adoption engineer, **I want** a whole-stack status grid **so that** I see Runtime, Gateway, CC, SDK health in one place.

**Acceptance criteria:**
- Poll every 10s while on step (configurable)
- Per-layer: health, last check time, error detail
- SDK row reflects last smoke test if run
- Stale indicator if poll fails 3× consecutive

---

### Step 10 — LLM test selection

**As** an adoption engineer, **I want** to choose which capability (and resolved model) to test **so that** validation matches the client's intended use case.

**Acceptance criteria:**
- Fetch Gateway `/api/v1/capabilities` (via Studio BFF with service key)
- Operator selects **capability** (required); optional **model override** if Gateway exposes models
- Show resolved route preview (capability → model from Gateway registry)
- Save selection to `workflow-state.json` and manifest `validation.test_capability`
- Default: `chat` for pack; `summarization` if use_case_interest includes document_summarisation
- "Quick smoke" button runs single SDK chat before full validation suite

**See:** [SPEC-llm-test-selection-v1.md](./SPEC-llm-test-selection-v1.md)

---

### Step 11 — Automated validation

**As** an adoption engineer, **I want** to run the full validation suite from the UI **so that** `deployment-report.json` is produced.

**Acceptance criteria:**
- Uses operator's LLM test selection for smoke/load checks
- Triggers `delivery-validate` / RM validate with manifest
- Progress bar per check from validation matrix
- Renders pass/fail summary; links to full JSON/MD report
- Exit code surfaced; failed checks expandable with logs

---

### Step 12 — Manual Control Centre checks

**As** an adoption engineer, **I want** an interactive CC checklist **so that** manual gates are recorded in deployment report.

**Acceptance criteria:**
- Checklist items from validation-suite-spec manual section
- Toggle each item; optional notes
- Deep link to Control Centre (`http://localhost:8002` or manifest URL)
- Persists to `deployment-report.json` → `manual_control_centre_checks`

---

### Step 13 — cp3 approval

**As** a delivery lead, **I want** to approve lab validation **so that** ship discussion can proceed.

**Acceptance criteria:**
- Requires automated validation passed (or override with reason — admin only)
- Requires manual checklist complete (or documented exceptions)
- Records cp3 with actor

---

### Step 14 — Ship prep & cp4

**As** a delivery lead, **I want** ship checklist and cp4 **so that** handover is gated.

**Acceptance criteria:**
- Production profile/model summary from assessment
- cp4 approval capture
- Export pipeline CSV from wizard

---

### Step 15 — Cursor certify & troubleshoot (cross-cutting)

**As** an adoption engineer, **I want** AI-assisted certification and diagnosis **so that** I resolve issues faster and improve the platform.

**Acceptance criteria:**
- Available from Deploy, Live Status, Validation steps
- Certify: structured verdict with evidence
- Troubleshoot: streaming agent response; suggested fixes scoped by repo
- PIR draft on platform improvement suggestions
- Operator confirms before any suggested command execution

---

## 3. Non-functional requirements

| NFR | Target |
|-----|--------|
| Accessibility | Terminal: symbols + text labels; documented key bindings |
| Auth | Local OS user; `STUDIO_OPERATOR` for audit actor; optional key for `serve-eoi` |
| Performance | Step navigation < 200ms; status poll batch < 2s |
| Terminal | Windows Terminal / WSL2 / modern Linux/macOS; min 100×24 |

---

## 4. Error states

| Scenario | UX |
|----------|-----|
| Schema validation fail | Inline field errors; block Next |
| Deploy job fail | Red banner + logs + Cursor troubleshoot CTA |
| Gateway unreachable | Status grid degraded; retry button |
| Validation check fail | Expandable row + remediation hint from spec |
| Cursor agent timeout | Retry; fallback to manual runbook link |

---

## 5. Empty states

| Step | Empty state |
|------|-------------|
| Leads inbox | "No leads yet — share EOI API or use demo form" |
| Assessment | "Complete internal questionnaire to run assessment" |
| Manifest | "Complete cp2 to configure playground kit" |
| Deployment report | "Run automated validation to see results" |

---

## 6. Implementation checklist

- [ ] Map each story to routes in [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md)
- [ ] Map steps to state in [SPEC-wizard-state-model-v1.md](./SPEC-wizard-state-model-v1.md)
- [ ] UX wireframes in [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md)

---

**See also:** [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md), [PLAN-implementation-phases-v1.md](./PLAN-implementation-phases-v1.md)
