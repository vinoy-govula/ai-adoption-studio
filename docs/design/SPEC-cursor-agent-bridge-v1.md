# SPEC — Cursor Agent Bridge v1

**Status:** Draft for review  
**Parent spec:** [ADR-002-cursor-agent-certification.md](./ADR-002-cursor-agent-certification.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. Purpose

Server-side bridge between Adoption Studio wizard and Cursor SDK for deployment certification, troubleshooting, and Platform Improvement Records (PIRs).

---

## 2. Dependencies

```toml
# pyproject.toml (optional extra)
cursor-sdk = ">=0.1.0"  # pin at implementation time
```

Config:

| Variable | Purpose |
|----------|---------|
| `STUDIO_CURSOR_API_KEY` | Cursor API authentication |
| `STUDIO_CURSOR_WORKSPACE_ROOT` | Parent `AI Adoption/` path for local runtime |
| `STUDIO_CURSOR_MODEL` | Default agent model (e.g. composer-2.5) |

---

## 3. CursorAgentBridge API

```python
class CursorAgentBridge:
    async def certify(
        self,
        lead_id: str,
        *,
        manifest: dict,
        deployment_report: dict | None,
        status_snapshot: dict,
    ) -> CertificationVerdict: ...

    async def troubleshoot(
        self,
        lead_id: str,
        *,
        context: TroubleshootContext,
        message: str,
        run_id: str | None = None,
    ) -> AsyncIterator[str]: ...  # stream tokens

    async def suggest_pir(
        self,
        lead_id: str,
        *,
        context: dict,
    ) -> str: ...  # markdown
```

---

## 4. Prompt assembly

### System context (all modes)

Inject file contents or summaries from:

- `platform-architecture` skill
- `observability-standards` skill
- `security-governance-review` skill
- Gateway/RM/CC/SDK boundary rules
- Deliverable Set E summary

### Certify mode user prompt template

```markdown
Certify this playground deployment against Deliverable Set E and validation-suite-spec-v1.

Lead: {lead_id} (org redacted)
Manifest status: {status}
Deployment report: {summary}
Live status: {overall}
Test capability: {capability}

Output JSON matching certification-verdict.v1 schema.
Do not suggest code changes; verdict only.
```

### Troubleshoot mode

Include:

- Failed check name + message
- Last 100 lines deploy/validate log (redacted)
- Manifest deployment preset
- Operator question

---

## 5. certification-verdict.v1 schema (Studio-owned)

```json
{
  "schema_version": "1.0.0",
  "verdict": "pass|conditional|fail",
  "confidence": 0.92,
  "evidence": [
    { "source": "deployment-report.checks[3]", "finding": "..." }
  ],
  "conditions": ["Manual CC checklist item cc_audit not verified"],
  "recommended_actions": [],
  "generated_at": "iso8601"
}
```

Store: `{lead_id}/cursor-runs/{run_id}-verdict.json`

---

## 6. Redaction policy

Before any agent call:

| Data | Action |
|------|--------|
| API keys | Replace with `[REDACTED]` |
| contact_email | Hash or truncate |
| `.env` paths | Omit contents |
| Full logs | Truncate to 100 lines; strip key patterns |

---

## 7. Guardrails

| Rule | Enforcement |
|------|-------------|
| Read-only certify | Prompt + parse verdict only |
| No auto-exec | Commands printed to terminal; operator copies/runs manually |
| Local runtime default | `local={"cwd": workspace_root}` |
| Audit | Persist run metadata JSON |
| Boundary fence | System prompt lists MUST NOT ownership violations |

---

## 8. Web UI integration

| Route | Purpose |
|-------|---------|
| `POST /api/leads/{id}/cursor/certify` | Start certify job |
| `POST /api/leads/{id}/cursor/troubleshoot` | Stream troubleshoot |
| `POST /api/leads/{id}/cursor/pir` | PIR draft |
| `GET /api/leads/{id}/cursor/runs` | Run history |

CursorAssistPanel MonsterUI modal on wizard steps 8–13.

---

## 9. Feedback loop

PIR output uses [PIR-template-v1.md](./PIR-template-v1.md). Operator copies to appropriate repo issue or docs folder — no auto-commit.

Suggested targets:

| Finding type | Target repo |
|--------------|-------------|
| Validation threshold | ai-runtime-manager |
| Capability gap | ai-gateway |
| Preset mapping | ai-runtime-manager preset-catalog |
| UX friction | ai-adoption-studio |

---

## 10. Implementation checklist

- [ ] `adapters/cursor_agent.py`
- [ ] `services/certification_service.py`
- [ ] `models/certification_verdict.py`
- [ ] `cli/commands/cursor_cmd.py`
- [ ] `tui/screens/cursor_assist_modal.py`
- [ ] Redaction utility `services/redaction.py`

---

**See also:** [PIR-template-v1.md](./PIR-template-v1.md), Cursor SDK docs
