# PLAN — Operator Experience Improvements v1

**Status:** Draft for review  
**Date:** 2026-07-04  
**Owner:** `ai-adoption-studio` (with a companion change in `ai-gateway`)  
**Specs:** [SPEC-operator-single-command-v1.md](./SPEC-operator-single-command-v1.md) · [SPEC-deployment-orchestration-v1.md](./SPEC-deployment-orchestration-v1.md)  
**ADRs:** [ADR-005 (studio)](./ADR-005-operator-startup-and-console.md) · [ADR-006 (gateway)](../../../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md)

---

## Objective

An operator runs **one command** and gets a working stack: dependencies started automatically, the one required key stable across restarts, and a read-only console to watch progress — no PTY, no secret-management machinery.

### Decisions locked in

- Single entrypoint lives at the **`AI Adoption/` root** (cleaner, one command spans repos).
- Credentials are **static config**, not managed secrets (internal tool). Only the Gateway bearer token is technically required.
- Gateway gains a **startup bootstrap-key seed** so the token survives restarts ([ADR-006](../../../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md)).
- Console is **read-only SSE + allow-listed command palette**; no interactive terminal.

---

## Delivery status

| Phase | Status |
|-------|--------|
| Phase 1 — Gateway startup bootstrap-key seed | **Delivered** (ai-gateway; 8 tests) |
| Phase 2 — Root single-command orchestrator | **Delivered** (`studio up/down/status/logs`; 8 tests) |
| Phase 3 — Read-only operator console | **Delivered** (SSE stream + allow-listed palette; 7 tests). Wiring the SSE console + palette into the wizard deploy page remains. |
| Phase 4 — Docs & cleanup | In progress (READMEs updated) |

## Phased delivery

### Phase 1 — Gateway startup bootstrap-key seed (`ai-gateway`)

*Unblocks "generate once, reuse every time". Do first.* **Delivered.**

| Step | Change | File |
|------|--------|------|
| 1.1 | Add `bootstrap_*` settings | `src/ai_gateway/config.py` |
| 1.2 | Add lifespan startup hook that seeds admin user + API key when `bootstrap_enabled` and `app_env == "development"`; idempotent; never logs the key | `src/ai_gateway/main.py` (+ small helper in `auth/`) |
| 1.3 | Document `.env.example` keys (`BOOTSTRAP_ENABLED`, `BOOTSTRAP_ADMIN_KEY`, ...) | `ai-gateway/.env.example`, `README.md` |
| 1.4 | Tests: seed on startup, idempotent re-seed, refuses in non-development, no key in logs | `tests/` |

**Gate:** security-standards + `70-adr-required` review (auth change). ADR-006 must be Accepted.

### Phase 2 — Root single-command orchestrator (`AI Adoption/` root)

| Step | Change | File |
|------|--------|------|
| 2.1 | `scripts/orchestrate.py` — `up`/`down`/`status`/`logs`; prerequisite checks; idempotent; health-gated (reuse `_wait_for_health` pattern) | `scripts/orchestrate.py` |
| 2.2 | Thin wrappers | `studio.ps1`, `studio.bat`, `studio` |
| 2.3 | `ensure_config()` writes `ai-adoption-studio/.env` once from template | `ai-adoption-studio/.env.example` |
| 2.4 | Tests: config idempotency, prerequisite checks, mocked-subprocess `up` ordering + failure path | `ai-adoption-studio/tests/` |

**Depends on:** Phase 1 (for zero-copy key); falls back to existing hybrid bootstrap if `bootstrap_enabled` is off.

### Phase 3 — Read-only operator console (`ai-adoption-studio`)

| Step | Change | File |
|------|--------|------|
| 3.1 | SSE endpoint `GET /api/jobs/{id}/stream` with polling fallback | `routes/api_jobs.py` |
| 3.2 | `deploy_log_viewer.py` consumes SSE (HTMX SSE ext); stays read-only | `components/deploy_log_viewer.py` |
| 3.3 | Allow-listed command palette wired to `JobRunner.spawn` (deps_up / health / deploy_lab / validate / tail) | new component + `routes/` |
| 3.4 | Tests: SSE stream tails log; palette actions spawn only allow-listed jobs | `tests/` |

**Depends on:** none beyond existing `JobRunner`; can proceed in parallel with Phase 2.

### Phase 4 — Docs & cleanup

| Step | Change |
|------|--------|
| 4.1 | Replace Studio README "Quick start" with `studio up` |
| 4.2 | Update deployment-catalog README to reference the orchestrator + stable key |
| 4.3 | Link new docs from the design README index |

---

## Sequencing

```text
Phase 1 (gateway seed) ──► Phase 2 (root orchestrator) ──► Phase 4 (docs)
                       └──► Phase 3 (console, parallel) ──┘
```

---

## Risks & guardrails

| Risk | Mitigation |
|------|------------|
| Studio absorbing runtime lifecycle | Orchestration stays in root ops layer; shells to `deployment-catalog`; Studio `services/*` unchanged ([ADR-001](./ADR-001-wizard-orchestration-boundaries.md)) |
| Known static key leaking to non-dev | Hard gate to `app_env == "development"`; disabled by default; never logged |
| Console becoming an RCE surface | No PTY; fixed allow-list only; no free-form command entry |
| Cross-repo coupling | Orchestrator degrades gracefully if Gateway seed is disabled |

---

## Definition of done

- `studio up` from clean checkouts → Studio browsable, all layers healthy, in one command.
- Gateway restart does **not** invalidate the operator's key.
- Operator watches deploy/validate output live in-app; cannot execute arbitrary commands.
- Tests green in each repo; ADR-005 and ADR-006 Accepted.

---

**See also:** [PLAN-implementation-phases-v1.md](./PLAN-implementation-phases-v1.md) (wizard delivery), [TEST-plan-wizard-v1.md](./TEST-plan-wizard-v1.md)
