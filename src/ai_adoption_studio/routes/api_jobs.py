"""Job polling and streaming API routes."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from starlette.responses import FileResponse, StreamingResponse

from ai_adoption_studio.components.deploy_log_viewer import deploy_log_viewer, job_progress
from ai_adoption_studio.models.job_record import JobStatus
from ai_adoption_studio.services.job_runner import JobRunner
from ai_adoption_studio.services.store import LeadStore

_TERMINAL = {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}


def _resolve_lead(store: LeadStore, jobs: JobRunner, job_id: str, lead_id: str) -> str | None:
    if lead_id:
        return lead_id
    for lid in store._store.list_lead_ids():
        try:
            jobs.get_job(lid, job_id)
            return lid
        except FileNotFoundError:
            continue
    return None


async def sse_log_events(
    jobs: JobRunner,
    lead_id: str,
    job_id: str,
    *,
    poll_interval: float = 1.0,
    sleep=asyncio.sleep,
) -> AsyncIterator[str]:
    """Yield SSE frames for a job log until the job reaches a terminal state."""
    sent = 0
    while True:
        text = jobs.tail_log(lead_id, job_id, tail=100_000)
        lines = text.splitlines()
        for line in lines[sent:]:
            yield f"data: {line}\n\n"
        sent = len(lines)
        try:
            job = jobs.get_job(lead_id, job_id)
        except FileNotFoundError:
            yield "event: error\ndata: job not found\n\n"
            return
        if job.status in _TERMINAL:
            yield f"event: done\ndata: {job.status.value}\n\n"
            return
        await sleep(poll_interval)


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

    @app.get("/api/jobs/{job_id}/log/download")
    async def job_log_download(job_id: str, lead_id: str = ""):
        resolved = _resolve_lead(store, jobs, job_id, lead_id)
        if resolved is None:
            return {"success": False, "error": "Job not found"}
        job = jobs.get_job(resolved, job_id)
        path = store._store.lead_dir(resolved) / job.log_path
        if not path.exists():
            return {"success": False, "error": "Log not found"}
        return FileResponse(
            path,
            media_type="text/plain",
            filename=f"{resolved}-{job_id}.log",
        )

    @app.get("/api/jobs/{job_id}/stream")
    async def job_stream(job_id: str, lead_id: str = "", k: str = ""):
        resolved = _resolve_lead(store, jobs, job_id, lead_id)
        if resolved is None:
            return {"success": False, "error": "Job not found"}
        return StreamingResponse(
            sse_log_events(jobs, resolved, job_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
