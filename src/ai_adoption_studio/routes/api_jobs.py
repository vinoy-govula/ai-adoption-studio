"""Job polling API routes."""

from __future__ import annotations

from ai_adoption_studio.components.deploy_log_viewer import deploy_log_viewer, job_progress
from ai_adoption_studio.services.job_runner import JobRunner
from ai_adoption_studio.services.store import LeadStore


def register_api_job_routes(app, store: LeadStore, jobs: JobRunner) -> None:
    @app.get("/api/jobs/{job_id}")
    async def job_status(job_id: str, lead_id: str = ""):
        if not lead_id:
            for lid in store._store.list_lead_ids():
                try:
                    job = jobs.get_job(lid, job_id)
                    return job_progress(job)
                except FileNotFoundError:
                    continue
            return {"success": False, "error": "Job not found"}
        job = jobs.get_job(lead_id, job_id)
        return job_progress(job)

    @app.get("/api/jobs/{job_id}/log")
    async def job_log(job_id: str, lead_id: str = "", tail: int = 50):
        if not lead_id:
            for lid in store._store.list_lead_ids():
                try:
                    job = jobs.get_job(lid, job_id)
                    text = jobs.tail_log(lid, job_id, tail=tail)
                    return deploy_log_viewer(lid, job, text)
                except FileNotFoundError:
                    continue
            return {"success": False, "error": "Job not found"}
        job = jobs.get_job(lead_id, job_id)
        text = jobs.tail_log(lead_id, job_id, tail=tail)
        return deploy_log_viewer(lead_id, job, text)
