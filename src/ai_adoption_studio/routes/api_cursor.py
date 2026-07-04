"""Cursor agent API routes."""
# ruff: noqa: F405

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.adapters.cursor_agent import CursorAgentBridge
from ai_adoption_studio.services.certification_service import CertificationService
from ai_adoption_studio.services.store import LeadStore


VERDICT_EXPLANATIONS = {
    "pass": "Cursor Assist found enough evidence to proceed without additional conditions.",
    "conditional": "The deployment can continue, but listed conditions should be cleared before lab sign-off.",
    "fail": "A blocking issue was found. Resolve the findings before continuing the deployment workflow.",
}


def register_api_cursor_routes(
    app,
    store: LeadStore,
    bridge: CursorAgentBridge,
    certify: CertificationService,
) -> None:
    @app.post("/api/leads/{lead_id}/cursor/certify")
    async def cursor_certify(lead_id: str):
        verdict = await certify.certify(lead_id)
        explanation = VERDICT_EXPLANATIONS.get(
            verdict.verdict.lower(),
            "Review the evidence and recommended actions before making a deployment decision.",
        )
        return Card(
            H4(f"Verdict: {verdict.verdict}", cls="font-semibold"),
            P(explanation, cls="text-sm text-slate-600 mt-1"),
            Div(
                Strong("Confidence: "),
                Span(f"{verdict.confidence:.0%}"),
                P(
                    "Confidence reflects how complete the available manifest, validation, status, "
                    "and audit evidence looked to Cursor Assist.",
                    cls="text-xs text-slate-500 mt-1",
                ),
                cls="my-3",
            ),
            Div(
                H5("Conditions to clear", cls="font-semibold text-sm"),
                Ul(*[Li(c) for c in verdict.conditions])
                if verdict.conditions
                else P("No open conditions returned.", cls="text-sm text-slate-600"),
                cls="mb-3",
            ),
            Div(
                H5("Evidence reviewed", cls="font-semibold text-sm"),
                Ul(*[Li(f"{item.source}: {item.finding}") for item in verdict.evidence])
                if verdict.evidence
                else P("No detailed evidence returned.", cls="text-sm text-slate-600"),
                cls="mb-3",
            ),
            Div(
                H5("Recommended actions", cls="font-semibold text-sm"),
                Ul(*[Li(action) for action in verdict.recommended_actions])
                if verdict.recommended_actions
                else P("Continue with the wizard gates below.", cls="text-sm text-slate-600"),
            ),
        )

    @app.post("/api/leads/{lead_id}/cursor/troubleshoot")
    async def cursor_troubleshoot(lead_id: str, failed_check: str = ""):
        log = ""
        jobs_dir = store._store.lead_dir(lead_id) / "jobs"
        if jobs_dir.exists():
            logs = sorted(jobs_dir.glob("*.log"), reverse=True)
            if logs:
                log = logs[0].read_text(encoding="utf-8", errors="replace")
        chunks = []
        async for token in bridge.troubleshoot(
            lead_id,
            context={"failed_check": failed_check, "log_excerpt": log},
            message="Diagnose failure",
        ):
            chunks.append(token)
        return Pre("".join(chunks), cls="text-sm bg-slate-100 p-3 rounded")

    @app.post("/api/leads/{lead_id}/cursor/pir")
    async def cursor_pir(lead_id: str):
        md = await bridge.suggest_pir(lead_id, context={"finding": "Validation friction"})
        return render_md(md)

    @app.get("/api/leads/{lead_id}/cursor/runs")
    async def cursor_runs(lead_id: str):
        runs = bridge.list_runs(lead_id)
        rows = [Tr(Td(r.get("run_id", "")), Td(r.get("mode", "")), Td(r.get("created_at", ""))) for r in runs]
        return Table(cls="w-full text-sm")(Thead(Tr(Th("Run"), Th("Mode"), Th("At"))), Tbody(*rows))
