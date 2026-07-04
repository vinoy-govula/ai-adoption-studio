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

---

## 6. Log streaming

HTMX poll `GET /api/jobs/{id}/log?tail=50` every 2s into DeployLogViewer component.

Phase 2 (optional): SSE `GET /api/jobs/{id}/stream`

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

---

**See also:** [SPEC-validation-ui-v1.md](./SPEC-validation-ui-v1.md), [ai-delivery-validator README](../../ai-delivery-validator/README.md)
