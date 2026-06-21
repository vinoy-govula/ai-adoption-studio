# UX — Component Catalog v1

**Status:** Draft for review  
**Parent spec:** [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md)  
**Repository owner:** `ai-adoption-studio`  
**Stack:** FastHTML + HTMX + **MonsterUI**

---

## 1. WizardStepper

Vertical sidebar step list. MonsterUI list/nav styling + checkmark icons for complete steps.

| Prop | Type | Description |
|------|------|-------------|
| `steps` | list[StepMeta] | id, label, status |
| `current` | str | Active step id |
| `lead_id` | str | HTMX href base |

HTMX: clicking completed step `hx-get`s step partial.

---

## 2. GoalBanner

MonsterUI `Card` header strip: title, goal text, est. time, approver (RACI from BRD).

---

## 3. QuestionField

Maps question-set JSON to MonsterUI form helpers:

| question.type | MonsterUI |
|---------------|-----------|
| `text`, `email` | `LabelInput` |
| `textarea` | `LabelTextArea` |
| `boolean` | `LabelCheckbox` |
| `select` | `LabelSelect` |
| `multi_select` | Checkbox group in `Fieldset` |
| `integer` | `LabelInput` with validation |

---

## 4. DynamicForm

Full form from question-set; groups by `dimension` using `Fieldset` + `Legend`. HTMX POST to step route.

---

## 5. ArtifactPanel

Collapsible MonsterUI `Details` or accordion: Summary tab + JSON `<pre>` + schema validation badge.

---

## 6. CheckpointBanner

cp1–cp4: `LabelInput` approver email, `LabelTextArea` notes, primary `Button` with HTMX confirm pattern.

---

## 7. RecommendationCard

MonsterUI `Card`: pack, confidence badge, readiness scores. Expandable `rule_trace` table. `Alert` when architect review required.

---

## 8. BrandingForm

`LabelInput` / `LabelTextArea` for slug, welcome, logo URL, demo prompts, public URL, TTL.

---

## 9. DeployLogViewer

`<pre>` or MonsterUI `Code` block inside `Card`; HTMX poll `GET /api/jobs/{id}/log?tail=50` every 2s.

---

## 10. StatusGrid

Four MonsterUI cards in responsive `Grid`; HTMX poll every 10s. Stale/degraded `Alert` banner.

---

## 11. CapabilityPicker

`LabelSelect` from Gateway capabilities; read-only model preview `Static`; smoke test `Button`.

See [SPEC-llm-test-selection-v1.md](./SPEC-llm-test-selection-v1.md).

---

## 12. ValidationResults

MonsterUI table + progress; expandable failure rows; **Diagnose with Cursor** on failed checks.

---

## 13. ManualChecklist

Checkbox list with notes; link `A(href=control_centre_url)` to open CC in new tab.

---

## 14. CursorAssistPanel

MonsterUI `Modal`: Certify button, troubleshoot stream area, PIR markdown via `render_md()`.

---

## 15. JobProgress

Footer or inline progress bar; HTMX poll job status.

---

## 16. LeadsTable

Inbox: MonsterUI `Table` or card list with org, status, wizard progress %, submitted date.

---

## 17. File layout

```text
src/ai_adoption_studio/
  layouts/base.py           # Theme.slate.headers(), sidebar
  components/
    stepper.py
    goal_banner.py
    question_field.py
    dynamic_form.py
    artifact_panel.py
    recommendation_card.py
    deploy_log_viewer.py
    status_grid.py
    capability_picker.py
    validation_results.py
    manual_checklist.py
    cursor_assist_panel.py
    job_progress.py
  pages/
    inbox.py
    wizard.py
    wizard_steps/
```

---

## 18. Theme alignment

Use `Theme.slate` (or custom brand theme) consistent with Control Centre sidebar colours. Document tokens in `layouts/base.py` for future CC MonsterUI migration.

---

## 19. Implementation checklist

- [ ] Add `monsterui` dependency
- [ ] Refactor `layouts/base.py` from CDN Tailwind to MonsterUI headers
- [ ] Component tests via FastHTML test client

---

**See also:** [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md), [SPEC-dynamic-forms-v1.md](./SPEC-dynamic-forms-v1.md)
