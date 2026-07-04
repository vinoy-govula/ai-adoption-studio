# SPEC — Operator Single-Command Startup v1

**Status:** Draft for review  
**Date:** 2026-07-04  
**Repository owner:** `ai-adoption-studio`  
**Related:** [SPEC-deployment-orchestration-v1.md](./SPEC-deployment-orchestration-v1.md) · [ADR-005-operator-startup-and-console.md](./ADR-005-operator-startup-and-console.md) · [ADR-001-wizard-orchestration-boundaries.md](./ADR-001-wizard-orchestration-boundaries.md) · [PLAN-operator-experience-v1.md](./PLAN-operator-experience-v1.md)

---

## 1. Goal

An operator brings the entire local stack (dependencies + Studio) to a working state with **one command** — no manual env exports, no copy-pasted keys, no multi-terminal ritual.

**Success criterion:** from a clean set of sibling checkouts, `studio up` reaches a browsable Studio at `http://localhost:8010` with Gateway (`:8000`), Runtime Manager (`:8001`), and Control Centre (`:8002`) healthy in a single invocation.

This replaces the current onboarding flow, which requires:

- Manual `uv venv` / `uv sync` / 8+ `STUDIO_*` env exports ([README.md](../../README.md)).
- The deployment-catalog "hybrid" dance: partial `docker compose up`, `stop gateway`, local Gateway bootstrap in a separate terminal, then `--no-deps control-centre` ([deployment-catalog/README.md](../../../deployment-catalog/README.md)).
- Copy-pasting an ephemeral Gateway key into `deployment-catalog/.env` and `STUDIO_PLATFORM_API_KEY`.

---

## 2. Non-goals

- **No secret generation / rotation / vault machinery.** This is an internal tool; credentials are treated as static config (see §5).
- **No runtime lifecycle ownership inside Studio core.** Orchestration lives in a root-level ops layer that shells out to `deployment-catalog` compose. Studio services (`services/*`) are unchanged. (`gateway-boundaries`, `runtime-boundaries`, [ADR-001](./ADR-001-wizard-orchestration-boundaries.md).)
- **No interactive PTY / web shell.** See [SPEC-deployment-orchestration-v1.md §6](./SPEC-deployment-orchestration-v1.md).

---

## 3. Operator surface

Entrypoints live at the **`AI Adoption/` root** (spanning sibling repos) so a single command controls the whole stack. Thin OS wrappers delegate to one Python orchestrator so behaviour is identical across shells.

| Command | Effect |
|---------|--------|
| `studio up` | Ensure config → start deps → wait for health → start Studio |
| `studio down` | Stop Studio and the deployment-catalog stack |
| `studio status` | Print health of each layer + resolved URLs |
| `studio logs [service]` | Tail orchestrator / dependency logs |

Wrappers (each ~5 lines: resolve repo root, call the orchestrator):

- `studio.ps1` — PowerShell, primary on Windows
- `studio.bat` — cmd fallback
- `studio` — POSIX shell

All wrappers invoke: `uv run --project ai-adoption-studio python scripts/orchestrate.py <verb>`.

---

## 4. Orchestrator algorithm (`scripts/orchestrate.py`)

`up` sequence:

```text
1. check_prerequisites()      # §7 — docker, uv, python 3.13, ports, sibling checkouts
2. ensure_config()            # §5 — create ai-adoption-studio/.env from template if missing (idempotent)
3. compose_up()               # deployment-catalog: gateway-db, arm-db, arm, control-centre
4. ensure_gateway()           # start/seed Gateway (see ADR-006 — stable bootstrap key)
5. wait_for_health([...])     # reuse _wait_for_health pattern from ai-delivery-validator deploy_lab.py
6. launch_studio()            # uvicorn, env pre-populated from ai-adoption-studio/.env
7. print_status()             # status table + URLs
```

Design rules:

- **Idempotent** — safe to re-run. Already-running services are detected via `/healthz` and skipped.
- **Health gating** — reuse the `_wait_for_health(url, timeout)` polling already implemented in `ai-delivery-validator/.../services/deploy_lab.py`; do not re-invent.
- **Fail-fast with guidance** — on health timeout, print the failed layer, its URL, and the last N log lines; exit non-zero. No stack traces for expected failures.
- **Boundary** — the orchestrator only issues `docker compose` in `deployment-catalog` and launches processes; it never generates compose files or manages containers directly.

`down`: stop Studio process, then `docker compose down` in deployment-catalog.  
`status`: probe each `/healthz`, render the same table as the end of `up`.

---

## 5. Configuration model (no secret management)

**Decision:** this is an internal tool. The following are **static config**, not managed secrets.

| Value | Handling |
|-------|----------|
| `STUDIO_INTERNAL_API_KEY` | Fixed dev constant (existing default `"dev-key"` in `config.py`). Not generated. Only needs to match between server and server-rendered HTMX headers. |
| DB credentials | Static values in local `.env` (local Postgres containers). Not generated. |
| `STUDIO_PLATFORM_API_KEY` (Gateway token) | The **only** technically-required value. One stable, shared value reused by Studio and `deployment-catalog`. Made durable by the Gateway startup seed ([ADR-006](../../../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md)). |

Rules:

- `ensure_config()` writes `ai-adoption-studio/.env` **once** from a committed `.env.example` if absent; if present, it is left untouched (generate-once, reuse-every-time).
- `.env` is git-ignored (already in `.gitignore`) purely to avoid noise — **not** for security.
- With the Gateway startup seed, `GATEWAY_BOOTSTRAP_KEY` is a fixed, known dev constant shared by all local components. No generator service, no rotation, no vault.
- `config.py` already loads `.env` via `SettingsConfigDict(env_prefix="STUDIO_", env_file=".env")` — single source of truth; no code change required beyond documenting it.

---

## 6. File / directory layout

```text
AI Adoption/
  studio.ps1 / studio.bat / studio          # operator entrypoints (root)
  scripts/orchestrate.py                     # ops layer (root, not Studio core)
ai-adoption-studio/
  .env.example                               # template copied on first run
  .env                                       # generated once, git-ignored
deployment-catalog/
  docker-compose.yml                         # deps started by orchestrator (existing)
ai-gateway/
  (startup seed per ADR-006)                 # stable bootstrap key
```

---

## 7. Prerequisites verified by `up`

- `docker` + `docker compose` available.
- `uv` + Python 3.13 available.
- Ports `8000` / `8001` / `8002` / `8010` free (or remapped per `.env`).
- Sibling checkouts present: `ai-runtime-manager`, `ai-platform-sdk`, `ai-delivery-validator`, `deployment-catalog`.

Each missing prerequisite yields a single actionable message.

---

## 8. Testing

- Unit: `ensure_config()` idempotency (absent → created; present → untouched).
- Unit: `check_prerequisites()` with mocked `shutil.which` / socket probes.
- Integration (mocked subprocess): `up` issues compose + gateway + uvicorn in order and honours health gating; failure path exits non-zero with guidance.
- `-m live_stack`: real `up` reaches a healthy status table end-to-end.

---

## 9. Implementation checklist

- [ ] `studio.ps1`, `studio.bat`, `studio` (root)
- [ ] `scripts/orchestrate.py` (`up` / `down` / `status` / `logs`)
- [ ] `ai-adoption-studio/.env.example` template (all `STUDIO_*` + `GATEWAY_BOOTSTRAP_KEY` wiring)
- [ ] Reuse `_wait_for_health` helper
- [ ] Replace README "Quick start" with `studio up`
- [ ] Tests per §8

---

**See also:** [PLAN-operator-experience-v1.md](./PLAN-operator-experience-v1.md), [SPEC-deployment-orchestration-v1.md](./SPEC-deployment-orchestration-v1.md), [ADR-006 Gateway startup bootstrap key seed](../../../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md)
