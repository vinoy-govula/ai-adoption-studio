# SPEC — Validation UI v1

**Status:** Draft for review  
**Parent spec:** [validation-suite-spec-v1.md](../../ai-runtime-manager/docs/adoption-studio/validation-suite-spec-v1.md)  
**Application form:** FastHTML + MonsterUI — [ADR-004](./ADR-004-monsterui-web-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. Purpose

Wizard steps 11–12: trigger automated validation, render `deployment-report.json` in the browser, capture manual Control Centre checklist.

---

## 2. Validation trigger flow

```text
Operator clicks "Run full validation" (MonsterUI Button)
  → read workflow-state.validation.test_capability
  → DeploymentOrchestrator.validate(manifest, out_dir, capability=...)
  → HTMX polls GET /api/jobs/{id} every 2s
  → on complete: load deployment-report.json
  → render ValidationResults MonsterUI Card + table
  → advance workflow step on pass
```

---

## 3. Capability injection

Validation harness uses operator-selected capability for SDK smoke/load checks via `STUDIO_VALIDATION_CAPABILITY` env. See [SPEC-llm-test-selection-v1.md](./SPEC-llm-test-selection-v1.md).

---

## 4. deployment-report UI mapping

| Schema field | MonsterUI element |
|--------------|-------------------|
| `status` | Alert / badge (passed/failed/running) |
| `summary.*` | Stat cards in `Grid` |
| `checks[]` | Table with expandable rows (`Details` accordion) |
| `manual_control_centre_checks` | Checkbox list + notes |

Schema: [deployment-report.schema.json](../../ai-runtime-manager/docs/schemas/deployment-report.schema.json)

---

## 5. Manual Control Centre checklist

Interactive toggles mapped to `deployment-report.json` → `manual_control_centre_checks`. Deep link button to Control Centre URL.

Items from validation-suite-spec § Manual (checklist IDs: `cc_runtime_ready`, `cc_uptime`, `cc_streams`, `cc_total_requests`, `cc_rate_limited`, `cc_users`, `cc_api_keys`, `cc_audit`, `cc_capabilities`, `cc_models`).

---

## 6. cp3 gate logic

Enable cp3 approve when:

- `deployment-report.status == passed`
- Required automated checks passed per pack
- Manual checklist complete OR admin override with reason

---

## 7. Failed check remediation

Static hint map per check type. Failed rows show **Diagnose with Cursor** button → CursorAssist modal.

---

## 8. Implementation checklist

- [ ] `components/validation_results.py`
- [ ] `components/manual_checklist.py`
- [ ] `services/validation_ui_service.py`
- [ ] Wizard routes for steps 11–13

---

**See also:** [SPEC-deployment-orchestration-v1.md](./SPEC-deployment-orchestration-v1.md)
