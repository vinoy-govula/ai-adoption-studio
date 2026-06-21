# TEST — Plan Wizard v1

**Status:** Draft for review  
**Parent spec:** [PLAN-implementation-phases-v1.md](./PLAN-implementation-phases-v1.md)  
**Application form:** FastHTML + MonsterUI — [ADR-004](./ADR-004-monsterui-web-wizard-v1.md)

---

## 1. Test pyramid

| Layer | Scope | Tool |
|-------|-------|------|
| Unit | WizardService, form validator, redaction | pytest |
| HTTP/HTMX | Routes, auth, partial responses | pytest + Starlette/FastHTML test client |
| Integration | Adapters mocked | pytest + mock |
| E2E golden path | Full wizard | `@pytest.mark.live_stack` |

---

## 2. Unit tests

WizardService unlock rules, invalidation, FormValidator per question type, StatusAggregator degraded state, redaction.

---

## 3. HTTP tests

- 401 without API key on `/wizard/*`
- HTMX POST advances step; `#step-content` contains expected MonsterUI markers
- Job poll endpoint returns log fragment
- Smoke test endpoint updates workflow state

---

## 4. Golden path

Using [eoi-intent.example.json](../../ai-runtime-manager/docs/schemas/examples/eoi-intent.example.json):

```text
POST /api/v1/eoi → GET /wizard/{id} → qualify → assessment → cp2
→ kit → deploy (mock) → smoke → validate (mock) → cp3/cp4 → export
```

---

## 5. Manual QA

- [ ] MonsterUI theme renders; sidebar matches Control Centre feel
- [ ] All question-set fields render
- [ ] HTMX deploy log polling
- [ ] Capability picker from Gateway
- [ ] Cursor modal certify flow
- [ ] Keyboard/accessibility on forms

---

## 6. Coverage target

90%+ on wizard_service, form_validator; 80%+ on adapters (mocked).

---

**See also:** [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md)
