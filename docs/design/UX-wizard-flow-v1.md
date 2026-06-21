# UX — Wizard Flow v1

**Status:** Draft for review  
**Parent spec:** [PRD-operator-wizard-v1.md](./PRD-operator-wizard-v1.md)  
**Application form:** FastHTML + HTMX + MonsterUI — [ADR-004](./ADR-004-monsterui-web-wizard-v1.md)

---

## 1. Layout shell

```text
┌────────────────────────────────────────────────────────────────┐
│  Adoption Studio          [Lead: Acme Health]      [Export]   │
├──────────────┬─────────────────────────────────────────────────┤
│  STEPPER     │  STEP CONTENT (MonsterUI Card)                  │
│  (sidebar)   │  ┌ GoalBanner ─────────────────────────────┐   │
│              │  │ Goal + help + est. time + approver       │   │
│  1 EOI ✓     │  ├─────────────────────────────────────────┤   │
│  2 Qualify ✓ │  │ Main form / status / results             │   │
│  3 Assess ●  │  ├─────────────────────────────────────────┤   │
│  4 Run       │  │ ArtifactPanel (collapsible)              │   │
│  ...         │  └─────────────────────────────────────────┘   │
│              │  [← Back]  [Save draft]  [Next →]               │
├──────────────┴─────────────────────────────────────────────────┤
│  Cursor Assist drawer (Modal, steps 8–13)                      │
└────────────────────────────────────────────────────────────────┘
```

MonsterUI: `Container`, `Card`, `Grid`, theme from `Theme.slate.headers()`.

---

## 2. Step map

| # | Step ID | Label | Primary action | Gate |
|---|---------|-------|----------------|------|
| 0 | `inbox` | Leads | Open wizard | — |
| 1 | `eoi_review` | EOI Review | Acknowledge | cp0 exists |
| 2 | `qualify` | Qualify | Qualify lead | cp1 |
| 3 | `assessment_form` | Questionnaire | Save / Next | internal responses valid |
| 4 | `assessment_run` | Assessment | Run rules | report exists |
| 5 | `narrative` | Narrative | Generate | optional |
| 6 | `cp2_approve` | Client approval | Approve cp2 | cp2 |
| 7 | `branding_kit` | Playground kit | Generate manifest | manifest valid |
| 8 | `deploy_lab` | Deploy | Start deploy | cp2 + manifest |
| 9 | `live_status` | Live status | Refresh | deploy active |
| 10 | `llm_test_select` | Test LLM | Save + Quick smoke | capability selected |
| 11 | `validate` | Validate | Run suite | deploy healthy |
| 12 | `manual_cc` | CC checks | Complete checklist | — |
| 13 | `cp3_approve` | Lab sign-off | Approve cp3 | validation passed |
| 14 | `ship_prep` | Ship prep | Review production map | — |
| 15 | `cp4_approve` | Handover | Approve cp4 | cp4 |
| 16 | `export` | Export | CSV export | — |

---

## 3. Navigation rules

| Rule | Behavior |
|------|----------|
| **Next** | Validates step; HTMX POST; marks complete; swaps `#step-content` |
| **Back** | HTMX POST `/wizard/{id}/back`; no validation |
| **Stepper click** | HTMX GET completed steps only |
| **Save draft** | POST `/wizard/{id}/draft`; toast via MonsterUI notify |
| **Invalidation** | Warning `Alert` if assessment edited after cp2 |

---

## 4. HTMX interaction patterns

| Pattern | Use |
|---------|-----|
| `hx-post` + `hx-target="#step-content"` | Form submit within step |
| `hx-get` + `hx-trigger="every 10s"` | StatusGrid on live_status |
| `hx-get` + `hx-trigger="every 2s"` | JobProgress / DeployLogViewer |
| `hx-swap="outerHTML"` | Stepper sidebar refresh |
| `hx-indicator="#spinner"` | MonsterUI loading state |

---

## 5. Step wireframes

### LLM test selection (Step 10)

MonsterUI `LabelSelect` for capability, read-only model preview, `LabelTextArea` for prompt, `Button` for quick smoke. See [SPEC-llm-test-selection-v1.md](./SPEC-llm-test-selection-v1.md).

### Live status (Step 9)

StatusGrid: four MonsterUI cards in `Grid` columns — Runtime, Gateway, Control Centre, SDK.

### Validation (Step 11)

Progress bar + table of checks; failed rows expand with `Details`; Cursor button on failure.

### Narrative (Step 5)

`render_md()` inside `Card` for assessment markdown preview.

---

## 6. Cursor Assist drawer

MonsterUI modal on steps 8–13: Certify, Troubleshoot (stream to `#cursor-output`), PIR preview.

---

## 7. Accessibility

- Stepper: `aria-current="step"`
- MonsterUI form labels associated with inputs
- Status: icon + text (not color alone)
- WCAG 2.1 AA target

---

## 8. Implementation checklist

- [ ] `pages/wizard.py` — shell with stepper + `#step-content`
- [ ] `components/stepper.py`
- [ ] `pages/wizard_steps/` — per-step partials

---

**See also:** [UX-component-catalog-v1.md](./UX-component-catalog-v1.md)
