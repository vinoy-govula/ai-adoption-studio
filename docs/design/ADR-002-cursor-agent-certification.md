# ADR-002 — Cursor Agent Certification & Troubleshooting

**Status:** Proposed  
**Date:** 2026-06-21  
**Parent spec:** [ARCH-adoption-studio-wizard-v1.md](./ARCH-adoption-studio-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## Context

Operators need AI-assisted certification of lab deployments and troubleshooting of failures. The platform has extensive Skills and Rules across repos. Ad-hoc LLM calls from Studio would bypass guardrails and leak secrets.

---

## Decision

Integrate **Cursor SDK (Python `cursor-sdk`)** via a dedicated **Cursor Agent Bridge** service:

### Runtime

- **Local runtime** default: `cwd` = parent `AI Adoption/` folder (multi-repo access)
- **Cloud runtime:** disabled in v1 for deploy/certify flows (secrets/PII risk)

### Modes

| Mode | Trigger | Agent behavior |
|------|---------|----------------|
| **Certify** | Operator clicks "Certify deployment" | Read-only analysis; output structured verdict JSON |
| **Troubleshoot** | Failed deploy/validation check | Streaming diagnosis; ranked fixes by repo |
| **PIR draft** | Operator clicks "Suggest platform improvement" | Output PIR markdown from template |

### Guardrails (injected into agent prompt)

Load context from:

- `.cursor/skills/` — `platform-architecture`, `capability-routing`, `observability-standards`, `security-governance-review`
- Repo `AGENTS.md` and `.cursor/rules/*-boundaries.mdc` for gateway, RM, CC, SDK
- Sanitized artifacts only: manifest, deployment-report, workflow-state, redacted logs

**Never pass:** API keys, `.env` contents, full contact PII (hash/redact emails)

### Execution policy

- Agent is **read-only** for Certify mode
- Troubleshoot may **suggest** shell commands; Studio UI shows commands in copy box — operator must click "Run" (future: optional approved command runner)
- Agent outputs never auto-commit to any repo

### Persistence

Store under `{lead_id}/cursor-runs/{run_id}.json`:

```json
{
  "run_id": "uuid",
  "mode": "certify|troubleshoot|pir",
  "prompt_hash": "sha256",
  "verdict": "pass|conditional|fail",
  "linked_deployment_report_id": "uuid",
  "operator": "email",
  "created_at": "iso8601"
}
```

---

## Consequences

**Positive:**
- Consistent with Cursor ecosystem; Skills+Rules enforced
- Audit trail of AI-assisted decisions
- PIR loop improves RM validation, rules, docs

**Negative:**
- Requires `CURSOR_API_KEY` on operator machine/server
- Local runtime needs full repo checkout

---

## Rejected alternatives

| Alternative | Why rejected |
|-------------|--------------|
| `LOCAL_LLM_BASE_URL` for troubleshoot | No repo context; no Skills injection |
| Cloud Cursor with full logs | Secret/PII exposure |
| Auto-apply agent patches | Violates human-in-the-loop for platform changes |

---

## Implementation checklist

- [ ] `adapters/cursor_agent.py`
- [ ] `services/certification_service.py`
- [ ] `docs/design/PIR-template-v1.md` for output format
- [ ] Config: `STUDIO_CURSOR_API_KEY`, `STUDIO_CURSOR_WORKSPACE_ROOT`

---

**See also:** [SPEC-cursor-agent-bridge-v1.md](./SPEC-cursor-agent-bridge-v1.md)
