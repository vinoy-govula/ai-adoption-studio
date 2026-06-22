"""JSON/HTMX API routes for leads."""

from __future__ import annotations

import json
from typing import Any

from fasthtml.common import *  # noqa: F403

from ai_adoption_studio.adapters.delivery_validator import DeploymentOrchestrator
from ai_adoption_studio.adapters.gateway_client import GatewayClient
from ai_adoption_studio.components.capability_picker import capability_picker
from ai_adoption_studio.components.deploy_log_viewer import deploy_log_viewer, job_progress
from ai_adoption_studio.components.status_grid import status_grid
from ai_adoption_studio.config import settings
from ai_adoption_studio.models.workflow_state import SmokeResult
from ai_adoption_studio.pages.wizard_steps.render import render_step
from ai_adoption_studio.services.job_runner import JobRunner
from ai_adoption_studio.services.smoke_test_service import SmokeTestService
from ai_adoption_studio.services.status_aggregator import status_aggregator
from ai_adoption_studio.services.store import LeadStore
from ai_adoption_studio.services.wizard_service import WizardService


def register_api_lead_routes(app, store: LeadStore, wizard: WizardService, jobs: JobRunner, smoke: SmokeTestService) -> None:
    orchestrator = DeploymentOrchestrator()

    def _deps() -> tuple[LeadStore, WizardService, JobRunner, SmokeTestService]:
        from ai_adoption_studio.services.store import lead_store as active_store
        from ai_adoption_studio.services.wizard_service import wizard_service as active_wizard

        return active_store, active_wizard, jobs, smoke

    @app.get("/api/leads/{lead_id}/status")
    async def lead_status(lead_id: str):
        active_store, active_wizard, _, _ = _deps()
        snapshot = await status_aggregator.poll(lead_id)
        accept = ""
        if hasattr(app, "request"):
            pass
        return status_grid(lead_id, snapshot)

    @app.get("/api/leads/{lead_id}/capabilities")
    async def lead_capabilities(lead_id: str):
        try:
            caps = await GatewayClient().list_capabilities()
        except Exception as exc:
            return {"success": False, "error": str(exc)}
        return {"success": True, "data": caps}

    @app.post("/api/leads/{lead_id}/smoke-test")
    async def lead_smoke_test(lead_id: str, test_capability: str = "chat", test_prompt: str = ""):
        _, _, _, active_smoke = _deps()
        result = await active_smoke.run(lead_id, capability=test_capability, prompt=test_prompt)
        cls = "text-green-700" if result.status == "passed" else "text-red-700"
        return P(f"{result.status}: {result.message}", cls=cls)

    @app.post("/api/leads/{lead_id}/deploy")
    async def lead_deploy(lead_id: str):
        active_store, active_wizard, active_jobs, _ = _deps()
        lead_dir = active_store._store.lead_dir(lead_id)
        manifest_path = lead_dir / "playground-kit.manifest.json"
        if not manifest_path.exists():
            return await render_step(
                lead_id, "deploy_lab", store=active_store, wizard=active_wizard, jobs=active_jobs, message="Manifest missing."
            )

        async def _deploy(job) -> int:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "deploying"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            log_path = lead_dir / "jobs" / f"{job.job_id}.log"
            code = await orchestrator.deploy_lab(
                manifest_path,
                lead_dir / "staging",
                job_id=job.job_id,
                log_path=log_path,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "active" if code == 0 else "failed"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return code

        job = active_jobs.spawn(lead_id, "deploy", _deploy)
        active_wizard.set_active_job(lead_id, "deploy", job.job_id)
        return await render_step(
            lead_id, "deploy_lab", store=active_store, wizard=active_wizard, jobs=active_jobs, message=f"Deploy job {job.job_id} started."
        )

    @app.post("/api/leads/{lead_id}/validate")
    async def lead_validate(lead_id: str):
        active_store, active_wizard, active_jobs, _ = _deps()
        state = active_wizard.get_state(lead_id)
        lead_dir = active_store._store.lead_dir(lead_id)
        manifest_path = lead_dir / "playground-kit.manifest.json"
        capability = state.validation.test_capability

        async def _validate(job) -> int:
            log_path = lead_dir / "jobs" / f"{job.job_id}.log"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "validating"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            try:
                await orchestrator.validate(
                    manifest_path,
                    lead_dir,
                    job_id=job.job_id,
                    capability=capability,
                    log_path=log_path,
                )
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["status"] = "passed"
                manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                return 0
            except Exception:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["status"] = "failed"
                manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                return 1

        job = active_jobs.spawn(lead_id, "validate", _validate)
        active_wizard.set_active_job(lead_id, "validate", job.job_id)
        return await render_step(
            lead_id, "validate", store=active_store, wizard=active_wizard, jobs=active_jobs, message=f"Validation job {job.job_id} started."
        )
