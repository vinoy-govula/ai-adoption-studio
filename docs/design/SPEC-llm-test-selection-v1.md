# SPEC — LLM Test Selection v1

**Status:** Draft for review  
**Parent spec:** [PRD-operator-wizard-v1.md](./PRD-operator-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. Purpose

Allow the operator to **select which AI capability** (and optionally preview the resolved model) used when smoke-testing and validating a deployed playground stack — aligned with platform **capability-first** design.

Applications and validation must use `ai_platform.AIClient.chat(capability="...")`, not raw model IDs.

---

## 2. Operator experience (Step 10 — web wizard)

| Control | Description |
|---------|-------------|
| **Capability picker** | MonsterUI `LabelSelect` from Gateway |
| **Resolved model preview** | Read-only Static text |
| **Test prompt** | `LabelTextArea` |
| **Recommended preset** | Button applies default from assessment |
| **Quick smoke test** | HTMX POST `/api/leads/{id}/smoke-test` |
| **Save selection** | Persists to workflow-state + manifest |

---

## 3. Data sources

### Gateway capabilities

```
GET {GATEWAY_BASE_URL}/api/v1/capabilities
Authorization: Bearer {AI_PLATFORM_API_KEY}
```

Response envelope: `{"success": true, "data": [...]}`

Map to MonsterUI Select options: `capability_id`, display name, description.

### Default capability logic

| Condition | Default capability |
|-----------|-------------------|
| `use_case_interest` includes `document_summarisation` | `summarization` |
| `use_case_interest` includes `sql_analytics` | `sql-analysis` |
| Recommended pack = starter/business/enterprise | `chat` |
| Fallback | `chat` |

From EOI responses in `eoi-intent.json` + assessment recommendation.

### Resolved model preview

Optional dry-run via Gateway capabilities metadata — no separate BFF HTTP layer; `GatewayClient` called from service layer.

Phase 1: show capability's registered model from Gateway registry if exposed in capabilities API.

---

## 4. Persistence

### workflow-state.json

```json
"validation": {
  "test_capability": "chat",
  "test_model_override": null,
  "test_prompt": "Summarize this deployment in one sentence.",
  "selection_source": "recommended|operator",
  "last_smoke_result": { "status": "passed", "latency_ms": 842, "at": "..." }
}
```

### playground-kit.manifest.json extension

Add under `validation`:

```json
"validation": {
  "test_capability": "chat",
  "test_prompt": "...",
  "automated_checks": [...]
}
```

Propose schema addition to RM `playground-kit.manifest.schema.json` in Phase 3 (cross-repo ADR). Until then, Studio writes field; RM validation reads env var.

---

## 5. Quick smoke test

`POST /api/leads/{lead_id}/smoke-test` (HTMX from CapabilityPicker)

Server-side (service layer):

```python
from ai_platform import AIClient

client = AIClient(
    api_key=settings.platform_api_key,
    base_url=manifest_access_gateway_url,
)
response = client.chat(
    capability=workflow.validation.test_capability,
    messages=[{"role": "user", "content": workflow.validation.test_prompt}],
)
```

Record latency, token usage if available, update `last_smoke_result`.

---

## 6. Full validation suite integration

When running `delivery-validate`:

1. Set `STUDIO_VALIDATION_CAPABILITY={capability}` in subprocess env
2. RM `playground.py` SDK checks use env for `client.chat(capability=...)`
3. Store capability used in `deployment-report.json` → `targets.test_capability` (proposed field)

---

## 7. Console constraints

| Rule | Enforcement |
|------|-------------|
| Capability required before validate | Block Next on step 10 |
| No free-text model ID in v1 | Model override disabled unless Gateway admin mode |
| Show capability-first disclaimer | Static help text on step |

---

## 8. Error states

| Error | UX |
|-------|-----|
| Capabilities API 401 | "Configure STUDIO_PLATFORM_API_KEY" |
| Capabilities empty | "Gateway has no registered capabilities" |
| Smoke test fail | Show SDK error message; link to troubleshoot |
| Capability not routable | Red inline error on picker |

---

## 9. Cross-repo dependencies

| Repo | Change |
|------|--------|
| `ai-runtime-manager` | Read `STUDIO_VALIDATION_CAPABILITY` in SDK smoke checks |
| `ai-runtime-manager` | Optional schema field `validation.test_capability` |
| `ai-adoption-studio` | CapabilityPicker, smoke endpoint, workflow persistence |

---

## 10. Implementation checklist

- [ ] `tui/widgets/capability_picker.py`
- [ ] `services/smoke_test_service.py`
- [ ] `cli/commands/smoke.py`
- [ ] `components/capability_picker.py` wizard step 10
- [ ] Tests: default capability from EOI use cases

---

**See also:** [Platform SDK AGENTS.md](../../ai-platform-sdk/AGENTS.md), [capability-routing skill](../../../ai-gateway/.cursor/skills/capability-routing/SKILL.md)
