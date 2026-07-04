"""Deploy job log viewer with HTMX polling."""

from __future__ import annotations

from fasthtml.common import A, Button, Div, FT, H4, H5, Li, P, Pre, Progress, Span, Ul
from monsterui.all import Card

from ai_adoption_studio.components.htmx import operator_hx_headers
from ai_adoption_studio.config import settings
from ai_adoption_studio.models.job_record import JobRecord


_ERROR_MARKERS = (
    "error",
    "exception",
    "traceback",
    "failed",
    "filenotfounderror",
    "runtimeerror",
    "calledprocesserror",
    "exit ",
)

_ACTION_BUTTON_CLS = "uk-btn h-10 px-4 inline-flex items-center justify-center text-center"
_SECONDARY_BUTTON_CLS = f"{_ACTION_BUTTON_CLS} uk-btn-secondary"
_GHOST_BUTTON_CLS = f"{_ACTION_BUTTON_CLS} uk-btn-ghost"


def _log_insights(log_text: str) -> list[str]:
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    matches = [
        line
        for line in lines
        if any(marker in line.lower() for marker in _ERROR_MARKERS)
    ]
    return matches[-6:]


def _job_actions(lead_id: str, job: JobRecord) -> FT:
    auth = operator_hx_headers()
    return Div(cls="flex flex-wrap gap-2 mt-4")(
        Button(
            "Refresh terminal",
            cls=_SECONDARY_BUTTON_CLS,
            type="button",
            hx_get=f"/api/jobs/{job.job_id}?lead_id={lead_id}",
            hx_target=f"#job-progress-{job.job_id}",
            hx_swap="outerHTML",
            hx_headers=auth,
        ),
        A(
            "Download log",
            href=f"/api/jobs/{job.job_id}/log/download?lead_id={lead_id}",
            cls=_SECONDARY_BUTTON_CLS,
        ),
        Button(
            "Diagnose with Cursor",
            cls=_GHOST_BUTTON_CLS,
            type="button",
            hx_post=f"/api/leads/{lead_id}/cursor/troubleshoot",
            hx_vals='{"failed_check":"deploy_lab"}',
            hx_target=f"#job-diagnosis-{job.job_id}",
            hx_headers=auth,
        ),
    )


def deploy_log_viewer(lead_id: str, job: JobRecord, log_text: str) -> FT:
    auth = operator_hx_headers()
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
    insights = _log_insights(log_text)

    return Div(**attrs)(
        Card(
            Div(cls="flex justify-between mb-2")(
                Div(
                    H4("Deployment logs", cls="font-semibold"),
                    P(f"Job {job.job_id}", cls="text-xs text-slate-500"),
                ),
                Span(job.status.value, cls="text-sm capitalize"),
            ),
            Div(cls="rounded border bg-amber-50 p-3 mb-3")(
                H5("Failure intelligence", cls="font-semibold text-sm"),
                P(
                    "Most relevant log lines are shown here so you do not have to scan the full output.",
                    cls="text-xs text-slate-600 mb-2",
                ),
                Ul(*[Li(line) for line in insights], cls="text-xs")
                if insights
                else P("No error lines found yet. Open or download the full log for raw output.", cls="text-xs"),
            ),
            _job_actions(lead_id, job),
            Pre(
                log_text or "(waiting for output...)",
                cls="text-xs bg-slate-900 text-green-200 p-3 rounded overflow-auto max-h-80 whitespace-pre-wrap mt-3",
            ),
        )
    )


def deploy_log_viewer_sse(lead_id: str, job: JobRecord) -> FT:
    """Read-only console that streams the job log over SSE (no PTY).

    Uses the htmx SSE extension: each ``data:`` frame is appended to the log
    pane. Requires the SSE extension script (registered in ``theme_headers``).
    """
    connect = (
        f"/api/jobs/{job.job_id}/stream?lead_id={lead_id}&k={settings.internal_api_key}"
    )
    return Div(id=f"job-log-{job.job_id}", hx_ext="sse", sse_connect=connect)(
        Card(
            Div(cls="flex justify-between mb-2")(
                H4(f"Job {job.job_id}", cls="font-semibold"),
                Span(job.status.value, cls="text-sm capitalize"),
            ),
            Pre(
                job.message or "(streaming output...)",
                sse_swap="message",
                hx_swap="beforeend",
                cls="text-xs bg-slate-900 text-green-200 p-3 rounded overflow-auto max-h-64 whitespace-pre-wrap",
            ),
        )
    )


def job_progress(job: JobRecord, log_text: str = "") -> FT:
    auth = operator_hx_headers()
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
    pct = int(job.progress_pct)
    status_tone = {
        "queued": "text-blue-700",
        "running": "text-blue-700",
        "succeeded": "text-green-700",
        "failed": "text-red-700",
        "cancelled": "text-amber-700",
    }.get(job.status.value, "text-slate-700")
    insights = _log_insights(log_text)
    return Div(**attrs)(
        Card(
            Div(cls="flex justify-between items-start mb-2")(
                Div(
                    H4("Deployment progress", cls="font-semibold"),
                    P(
                        job.message or "Deployment job is starting. Waiting for first log output...",
                        cls="text-sm text-slate-600",
                    ),
                ),
                Div(cls=f"text-sm font-semibold capitalize {status_tone}")(
                    job.status.value,
                ),
            ),
            Progress(value=str(pct), max="100", cls="w-full"),
            P(f"{pct}% complete", cls="text-xs text-slate-500 mt-2"),
            _job_actions(job.lead_id, job),
            Div(id=f"job-diagnosis-{job.job_id}", cls="mt-3"),
            Div(cls="rounded border bg-amber-50 p-3 mt-4")(
                H5("Failure intelligence", cls="font-semibold text-sm"),
                P(
                    "Relevant failure lines are extracted from the deployment terminal below.",
                    cls="text-xs text-slate-600 mb-2",
                ),
                Ul(*[Li(line) for line in insights], cls="text-xs")
                if insights
                else P("No error lines found yet.", cls="text-xs"),
            ),
            Div(cls="mt-4")(
                Div(cls="flex justify-between items-center mb-2")(
                    H5("Deployment terminal", cls="font-semibold text-sm"),
                    Span(
                        "Auto-refreshing" if poll else "Final output",
                        cls="text-xs text-slate-500",
                    ),
                ),
                Pre(
                    log_text or "(waiting for output...)",
                    cls=(
                        "text-xs bg-slate-900 text-green-200 p-3 rounded "
                        "overflow-auto max-h-96 whitespace-pre-wrap"
                    ),
                ),
            ),
        )
    )
