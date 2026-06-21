# SPEC — Dynamic Forms v1

**Status:** Draft for review  
**Parent spec:** [UX-component-catalog-v1.md](./UX-component-catalog-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. Source files

| Form | Question set |
|------|--------------|
| Public EOI | `docs/eoi-question-set-v1.json` |
| Internal assessment | `docs/assessment-question-set-internal-v1.json` |

Load at startup; cache in memory; hot-reload in dev via file mtime check.

---

## 2. QuestionSet loader

```python
class QuestionSetLoader:
    def load(path: Path) -> QuestionSet: ...
    def get_by_id(set_id: str) -> QuestionSet: ...
```

Pydantic models: `Question`, `QuestionSet` mirroring JSON structure.

---

## 3. Rendering pipeline

```text
QuestionSet → group by dimension → DynamicForm → List[QuestionField]
POST → validate → map to responses dict → save artifact
```

---

## 4. Field mapping to artifacts

| Form | Output file | Key structure |
|------|-------------|---------------|
| EOI | `eoi-intent.json` | `responses.{question_id}` |
| Internal | `internal-responses.json` | flat `{question_id: value}` |

EOI also requires `consent` object (separate ConsentForm component).

---

## 5. Validation rules

| Rule | Implementation |
|------|----------------|
| `required` | Non-empty / at least one for multi_select |
| `options` | Value in enum list |
| `min` / `max` | Integer bounds |
| `max_length` | String length |
| `type=email` | Email format regex |

Return `{field_id: [error_messages]}` for inline display.

---

## 6. EOI API alignment

Public `POST /api/v1/eoi` accepts same keys as question set. Wizard EOI review displays stored record; optional "Edit EOI" admin mode regenerates form pre-filled.

---

## 7. Internal assessment merge

Rule engine expects EOI + internal fields per [rule-engine-spec-v1.md](../../ai-runtime-manager/docs/adoption-studio/rule-engine-spec-v1.md). `build_assessment_report(eoi, internal, ...)` unchanged.

---

## 8. Replace hardcoded forms

Remove hardcoded fields in legacy `main.py` / `studio.py`. Console wizard uses DynamicFormScreen + question set paths from config:

```python
EOI_QUESTION_SET = Path(__file__).parents[2] / "docs/eoi-question-set-v1.json"
INTERNAL_QUESTION_SET = Path(__file__).parents[2] / "docs/assessment-question-set-internal-v1.json"
```

Replace hardcoded FastHTML forms in `main.py` / `studio.py` with MonsterUI DynamicForm components.

---

## 9. Implementation checklist

- [ ] `services/question_set_loader.py`
- [ ] `components/dynamic_form.py`, `components/question_field.py`
- [ ] `services/form_validator.py`
- [ ] Tests: render all question types; validate required fields

---

**See also:** [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md)
