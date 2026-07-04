# ADR-005 — Single-Command Operator Startup and Read-Only Console

**Status:** Accepted  
**Date:** 2026-07-04  
**Repository owner:** `ai-adoption-studio`  
**Related:** [SPEC-operator-single-command-v1.md](./SPEC-operator-single-command-v1.md) · [SPEC-deployment-orchestration-v1.md](./SPEC-deployment-orchestration-v1.md) · [ADR-001-wizard-orchestration-boundaries.md](./ADR-001-wizard-orchestration-boundaries.md) · [Gateway ADR-006](../../../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md)

---

## Context

Operator onboarding today is a multi-terminal, copy-paste ritual:

- Manual `uv` setup and 8+ `STUDIO_*` env exports ([README.md](../../README.md)).
- The deployment-catalog "hybrid" flow: partial `docker compose up`, `stop gateway`, local Gateway bootstrap in a separate terminal, then `--no-deps control-centre` ([deployment-catalog/README.md](../../../deployment-catalog/README.md)).
- Gateway R1 auth is **in-memory**, so the bootstrap API key is lost on every restart and must be re-generated and re-pasted into `deployment-catalog/.env` and `STUDIO_PLATFORM_API_KEY`.

Operators also need to watch deploy/validate output. The instinctive ask — an embedded terminal — would add an arbitrary command-execution (RCE) surface to a governed platform, conflicting with audit boundaries.

---

## Decision

1. **One command.** Introduce `studio up / down / status / logs` — thin OS wrappers (`studio.ps1`, `studio.bat`, `studio`) over a single Python orchestrator (`scripts/orchestrate.py`), located at the **`AI Adoption/` root** so one command controls the whole stack. The orchestrator starts deployment-catalog dependencies, health-gates them, and launches Studio. See [SPEC-operator-single-command-v1.md](./SPEC-operator-single-command-v1.md).

2. **Ops layer, not Studio core.** Orchestration shells out to `deployment-catalog` compose and launches processes. It does **not** generate compose files or manage container lifecycle, and Studio's `services/*` are unchanged — preserving [ADR-001](./ADR-001-wizard-orchestration-boundaries.md), `gateway-boundaries`, and `runtime-boundaries`.

3. **Static config, not managed secrets.** For an internal tool, `STUDIO_INTERNAL_API_KEY`, DB credentials, and the Gateway token are treated as static config written once to a git-ignored local `.env`. No generator, no rotation, no vault.

4. **Durable Gateway token.** The single technically-required credential (the Gateway bearer token) is made stable across restarts by a Gateway startup seed — tracked as companion [Gateway ADR-006](../../../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md). This makes "generate once, reuse every time" hold.

5. **Read-only console, no PTY.** Studio provides an SSE-streamed, read-only log console plus an **allow-listed command palette** (Start deps / Health / Deploy / Validate / Tail) wired to vetted `JobRunner` jobs. No interactive shell, no free-form command entry. See [SPEC-deployment-orchestration-v1.md §6](./SPEC-deployment-orchestration-v1.md).

---

## Consequences

### Positive

- One-command onboarding; no key copy-paste; no ephemeral-key churn.
- No new secret-management machinery to build or defend.
- No RCE surface — console execution is limited to a fixed allow-list.
- Reuses existing patterns (`JobRunner`, `_wait_for_health`, `deploy_lab` compose calls).

### Negative

- Adds a root-level ops layer that spans sibling repos (must stay thin and boundary-respecting).
- Depends on the companion Gateway change ([ADR-006](../../../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md)) to fully remove key churn; until then the orchestrator falls back to the existing hybrid bootstrap.
- SSE adds a streaming endpoint to maintain alongside the polling fallback.

---

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| Embedded interactive PTY / web terminal | Arbitrary RCE surface; conflicts with governance/audit posture |
| Per-repo scripts only (status quo) | Does not deliver a single command; leaves multi-terminal ritual |
| Secret manager / vault for local creds | Over-engineered for an internal tool; not technically required |
| Orchestrator generates compose files | Violates Runtime Manager ownership; duplicates deployment-catalog |

---

**See also:** [PLAN-operator-experience-v1.md](./PLAN-operator-experience-v1.md)
