# SPEC — Deployment Orchestration v1

**Status:** Draft for review  
**Parent spec:** [ADR-001-wizard-orchestration-boundaries.md](./ADR-001-wizard-orchestration-boundaries.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. DeploymentOrchestrator adapter

```python
class DeploymentOrchestrator:
    async def generate_kit(
        self,
        lead_id: str,
        assessment_path: Path,
        branding: dict,
        output_dir: Path,
    ) -> Path: ...  # manifest path

    async def deploy_lab(
        self,
        manifest_path: Path,
        staging_dir: Path,
        *,
        job_id: str,
    ) -> int: ...  # exit code

    async def validate(
        self,
        manifest_path: Path,
        output_dir: Path,
        *,
        job_id: str,
        capability: str,
    ) -> Path: ...  # deployment-report path
```

---

## 2. Command templates

Configurable via `Settings`:

| Operation | Command |
|-----------|---------|
| generate_kit | `uv run delivery-generate-kit --assessment {assessment} --branding {branding} --output-dir {out}` |
| deploy_lab | `uv run delivery-deploy-lab --manifest {manifest} --staging-dir {lead_dir} --deployment-catalog-root {catalog}` |
| validate | `uv run delivery-validate --manifest {manifest} --output-dir {out}` |

Working directory: `ai-delivery-validator` repo (sibling path).

Environment forwarded:

- `RUNTIME_MANAGER_BASE_URL`
- `AI_PLATFORM_BASE_URL` (from manifest `access.public_url` when playground stage)
- `AI_PLATFORM_API_KEY`
- `DEPLOYMENT_CATALOG_ROOT`
- `STUDIO_VALIDATION_CAPABILITY` (from workflow state)

---

## 2.1 Two-phase lab deploy

`delivery-deploy-lab` runs compose in two phases when `skip_compose` is false:

1. **Platform stack** — `deployment-catalog/docker-compose.yml` when `deployment.infrastructure_stage` is not `developer`. Uses `--profile edge` when `deployment.edge_profile` is `platform-overlay`.
2. **Runtime stack** — RM-generated `deployment-artifacts/docker-compose.yml` under the lead artifact directory.

Developer stage skips platform compose (operator starts stack manually per deployment-catalog hybrid workflow).

Lab deploy gate: **cp2 approved only** (`can_deploy_lab`). cp3 remains post-validation sign-off.

---

## 3. Async execution

```text
Wizard Deploy step / `POST /api/leads/{id}/deploy`
  → create job record
  → asyncio.create_subprocess_exec(...)
  → stream stdout/stderr to jobs/{id}.log
  → LogPanel worker tails log
  → on complete: update manifest status, workflow step
```

---

## 4. Manifest status transitions

| Event | manifest.status |
|-------|-----------------|
| Kit generated | `draft` |
| Deploy started | `deploying` |
| Deploy success | `active` |
| Deploy fail | `failed` |
| Validate started | `validating` |
| Validate pass | `passed` |
| Validate fail | `failed` |

Update via RM helper or direct JSON patch in lead dir.

---

## 5. Prerequisites check (UI)

Before deploy button enabled in wizard:

- [ ] cp2 approved
- [ ] `playground-kit.manifest.json` valid
- [ ] `STUDIO_PLATFORM_API_KEY` configured
- [ ] Gateway reachable at manifest-resolved health URL
- [ ] Control Centre reachable at manifest-resolved health URL (path-based when edge overlay)

Displayed as MonsterUI checklist panel with infrastructure stage and edge profile summary.

> **Config, not secrets.** `STUDIO_INTERNAL_API_KEY`, DB credentials, and `STUDIO_PLATFORM_API_KEY` are **static config**, not managed secrets — this is an internal tool. The checklist reads them from the single local `.env`; it never generates or rotates them. The Gateway token is made durable by the Gateway startup seed ([ADR-006](../../../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md)). See [SPEC-operator-single-command-v1.md §5](./SPEC-operator-single-command-v1.md).

---

## 6. Operator console (read-only, no PTY)

**Decision:** No interactive terminal / PTY is exposed. The operator gets a **read-only streaming console** plus an **allow-listed command palette**. This preserves the audit/governance posture and avoids introducing an RCE surface. See [ADR-005](./ADR-005-operator-startup-and-console.md).

### 6.1 Streaming

Upgrade log delivery from HTMX 2s polling to **SSE**:

```text
GET /api/jobs/{id}/stream        # text/event-stream, tails jobs/{id}.log
```

- Fallback: the existing `GET /api/jobs/{id}/log?tail=N` polling remains for non-SSE clients.
- Component: extend `components/deploy_log_viewer.py` to consume SSE via the HTMX SSE extension; keep the read-only `Pre` render (no input element).

### 6.2 Command palette

A fixed, server-defined allow-list — never free-form input. Each action spawns a **vetted** job through the existing `JobRunner.spawn`; no user-supplied command string is ever passed to a shell.

| Palette action | Job type | Maps to |
|----------------|----------|---------|
| Start dependencies | `deps_up` | root `scripts/orchestrate.py up` (deps only) |
| Health check | `health` | `StatusAggregator.poll` |
| Deploy lab | `deploy_lab` | `DeploymentOrchestrator.deploy_lab` (existing) |
| Validate | `validate` | `DeploymentOrchestrator.validate` (existing) |
| Tail logs | `tail` | SSE stream of the selected job |

### 6.3 Security note

Because there is no PTY and no free-form command entry, the console introduces **no new execution surface** beyond the already-vetted delivery-validator subprocess calls in [ADR-001](./ADR-001-wizard-orchestration-boundaries.md).

---

## 7. Error handling

| exit_code | UX |
|-----------|-----|
| 0 | Success toast; advance step |
| 1 | Failed banner; show log; Cursor troubleshoot CTA |
| 2 | Config error; show env checklist |

---

## 8. Config additions

```python
class Settings(BaseSettings):
    delivery_validator_root: Path = Path("../ai-delivery-validator")
    deployment_catalog_root: Path = Path("../deployment-catalog")
    gateway_base_url: str = "http://localhost:8000"
    runtime_manager_base_url: str = "http://localhost:8001"
    control_centre_base_url: str = "http://localhost:8002"
    platform_api_key: str = ""
```

---

## 9. Implementation checklist

- [ ] `adapters/delivery_validator.py`
- [ ] `services/job_runner.py`
- [ ] Wire wizard step 8 deploy button
- [ ] Integration test with mocked subprocess
- [ ] SSE endpoint `GET /api/jobs/{id}/stream` (§6.1) with polling fallback
- [ ] Allow-listed command palette wired to `JobRunner.spawn` (§6.2)

---

**See also:** [SPEC-validation-ui-v1.md](./SPEC-validation-ui-v1.md), [ai-delivery-validator README](../../ai-delivery-validator/README.md)
