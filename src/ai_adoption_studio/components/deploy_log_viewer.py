"""Deploy job log viewer with HTMX polling."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.config import settings
from ai_adoption_studio.models.job_record import JobRecord


def deploy_log_viewer(lead_id: str, job: JobRecord, log_text: str) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    poll = job.status.value in {"queued", "running"}
    attrs: dict = {"id": f"job-log-{job.job_id}"}
    if poll:
        attrs.update(
            {
                "hx_get": f"/api/jobs/{job.job_id}/log?tail=50",
                "hx_trigger": "every 2s",
                "hx_swap": "outerHTML",
                "hx_headers": auth,
            }
        )

    return Div(**attrs)(
        Card(
            Div(cls="flex justify-between mb-2")(
                H4(f"Job {job.job_id}", cls="font-semibold"),
                Span(job.status.value, cls="text-sm capitalize"),
            ),
            Pre(log_text or "(waiting for output...)", cls="text-xs bg-slate-900 text-green-200 p-3 rounded overflow-auto max-h-64"),
        )
    )


def job_progress(job: JobRecord) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    poll = job.status.value in {"queued", "running"}
    attrs: dict = {"id": f"job-progress-{job.job_id}"}
    if poll:
        attrs.update(
            {
                "hx_get": f"/api/jobs/{job.job_id}",
                "hx_trigger": "every 2s",
                "hx_swap": "outerHTML",
                "hx_headers": auth,
            }
        )
    return Div(**attrs)(
        Card(
            P(f"Status: {job.status.value}", cls="font-medium"),
            P(job.message or "", cls="text-sm text-slate-600"),
            Progress(value=str(job.progress_pct), max="100"),
        )
    )
