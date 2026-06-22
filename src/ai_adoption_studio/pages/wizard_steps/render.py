"""Wizard step content renderers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403

from ai_adoption_studio.adapters.gateway_client import GatewayClient
from ai_adoption_studio.components.branding_form import branding_form
from ai_adoption_studio.components.capability_picker import capability_picker
from ai_adoption_studio.components.cursor_assist_panel import cursor_assist_panel
from ai_adoption_studio.components.deploy_log_viewer import deploy_log_viewer, job_progress
from ai_adoption_studio.components.dynamic_form import dynamic_form
from ai_adoption_studio.components.goal_banner import goal_banner
from ai_adoption_studio.components.manual_checklist import manual_checklist
from ai_adoption_studio.components.nav_buttons import step_nav
from ai_adoption_studio.components.recommendation_card import recommendation_card
from ai_adoption_studio.components.status_grid import status_grid
from ai_adoption_studio.components.validation_results import validation_results
from ai_adoption_studio.config import settings
from ai_adoption_studio.models.workflow_state import WorkflowState
from ai_adoption_studio.services.job_runner import JobRunner
from ai_adoption_studio.services.question_set_loader import question_set_loader
from ai_adoption_studio.services.status_aggregator import status_aggregator
from ai_adoption_studio.services.store import LeadStore
from ai_adoption_studio.services.validation_ui_service import validation_ui_service
from ai_adoption_studio.services.wizard_service import WizardService

CURSOR_STEPS = {"deploy_lab", "live_status", "llm_test_select", "validate", "manual_cc", "cp3_approve"}


async def render_step(
    lead_id: str,
    step_id: str,
    *,
    store: LeadStore,
    wizard: WizardService,
    jobs: JobRunner,
    message: str = "",
    errors: dict[str, list[str]] | None = None,
) -> FT:
    state = wizard.get_state(lead_id)
    eoi = store.get_eoi(lead_id)
    org = eoi.get("responses", {}).get("org_name", lead_id)
    parts: list[FT] = [goal_banner(step_id)]
    if message:
        parts.append(Alert(message, cls=AlertT.success))

    if step_id in CURSOR_STEPS:
        parts.append(cursor_assist_panel(lead_id))

    if step_id == "eoi_review":
        parts.append(_eoi_review(lead_id, eoi))
    elif step_id == "qualify":
        parts.append(_qualify_step(lead_id, eoi))
    elif step_id == "assessment_form":
        parts.append(await _assessment_form(lead_id, store, errors))
    elif step_id == "assessment_run":
        parts.append(_assessment_run(lead_id, store))
    elif step_id == "narrative":
        parts.append(await _narrative_step(lead_id, store))
    elif step_id == "cp2_approve":
        parts.append(_cp2_step(lead_id, store))
    elif step_id == "branding_kit":
        parts.append(branding_form(lead_id, state.branding))
    elif step_id == "deploy_lab":
        parts.append(await _deploy_step(lead_id, wizard, jobs, store))
    elif step_id == "live_status":
        parts.append(await _live_status(lead_id))
    elif step_id == "llm_test_select":
        parts.append(await _llm_test(lead_id, state))
    elif step_id == "validate":
        parts.append(await _validate_step(lead_id, wizard, jobs, store))
    elif step_id == "manual_cc":
        parts.append(_manual_cc_step(lead_id))
    elif step_id == "cp3_approve":
        parts.append(_cp3_step(lead_id, store))
    elif step_id == "ship_prep":
        parts.append(_ship_prep(lead_id, store))
    elif step_id == "cp4_approve":
        parts.append(_cp4_step(lead_id, store))
    elif step_id == "export":
        parts.append(_export_step(lead_id))
    else:
        parts.append(P(f"Unknown step: {step_id}"))

    parts.append(step_nav(lead_id, step_id))
    return Card(Div(*parts), cls="shadow-sm")


def _auth_form(lead_id: str, step_id: str, *fields: FT) -> FT:
    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    return Form(
        id=f"step-form-{step_id}",
        hx_post=f"/wizard/{lead_id}/{step_id}",
        hx_target="#step-content",
        hx_swap="innerHTML",
        hx_headers=auth,
    )(*fields)


def _eoi_review(lead_id: str, eoi: dict[str, Any]) -> FT:
    responses = eoi.get("responses", {})
    rows = [Tr(Td(k), Td(str(v))) for k, v in responses.items()]
    return _auth_form(
        lead_id,
        "eoi_review",
        P(f"Pipeline status: {eoi.get('pipeline_status', 'new')}"),
        Table(cls="w-full text-sm mb-4")(Tbody(*rows)),
        LabelCheckboxX("I have reviewed this EOI", name="acknowledged", value="true"),
    )


def _qualify_step(lead_id: str, eoi: dict[str, Any]) -> FT:
    return _auth_form(
        lead_id,
        "qualify",
        P(f"Current status: {eoi.get('pipeline_status', 'new_lead')}"),
        LabelInput("Actor email", name="actor", value="sales@example.com"),
    )


async def _assessment_form(
    lead_id: str,
    store: LeadStore,
    errors: dict[str, list[str]] | None,
) -> FT:
    qs = question_set_loader.get_internal()
    existing = store.get_internal_responses(lead_id) or {}
    return _auth_form(
        lead_id,
        "assessment_form",
        dynamic_form(qs, values=existing, errors=errors),
    )


def _assessment_run(lead_id: str, store: LeadStore) -> FT:
    report = store.get_assessment_report(lead_id)
    body = [P("Run the rule engine to produce assessment-report.json.")]
    if report:
        body.append(recommendation_card(report))
    return _auth_form(lead_id, "assessment_run", *body)


async def _narrative_step(lead_id: str, store: LeadStore) -> FT:
    report = store.get_assessment_report(lead_id)
    narrative_path = None
    if report:
        ref = report.get("llm_narrative_ref", "assessment-narrative.md")
        candidate = store._store.lead_dir(lead_id) / ref
        if candidate.exists():
            narrative_path = candidate
    content = ""
    if narrative_path:
        content = narrative_path.read_text(encoding="utf-8")
    md = render_md(content) if content else P("No narrative yet — click Next to generate.")
    return _auth_form(
        lead_id,
        "narrative",
        md,
        LabelCheckboxX("Regenerate narrative", name="regenerate", value="true"),
    )


def _cp2_step(lead_id: str, store: LeadStore) -> FT:
    report = store.get_assessment_report(lead_id)
    parts = []
    if report:
        parts.append(recommendation_card(report))
    parts.extend(
        [
            LabelInput("Approver email", name="actor", value="client@example.com"),
            LabelTextArea("Notes", name="notes"),
        ]
    )
    return _auth_form(lead_id, "cp2_approve", *parts)


async def _deploy_step(
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
    store: LeadStore,
) -> FT:
    manifest_path = store._store.lead_dir(lead_id) / "playground-kit.manifest.json"
    checks = [
        ("cp2 approved", wizard._cp2_approved(lead_id)),
        ("Manifest exists", manifest_path.exists()),
        ("Platform API key set", bool(settings.platform_api_key)),
    ]
    checklist = Ul(*[Li(f"{'✓' if ok else '✗'} {label}") for label, ok in checks])
    parts: list[FT] = [H4("Prerequisites"), checklist]

    state = wizard.get_state(lead_id)
    if state.active_jobs.deploy:
        job = jobs.get_job(lead_id, state.active_jobs.deploy)
        parts.append(job_progress(job))
        parts.append(deploy_log_viewer(lead_id, job, jobs.tail_log(lead_id, job.job_id)))

    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    parts.append(
        Button(
            "Start deploy",
            cls=ButtonT.primary,
            hx_post=f"/api/leads/{lead_id}/deploy",
            hx_target="#step-content",
            hx_swap="innerHTML",
            hx_headers=auth,
        )
    )
    return Div(*parts)


async def _live_status(lead_id: str) -> FT:
    snapshot = await status_aggregator.poll(lead_id)
    return status_grid(lead_id, snapshot)


async def _llm_test(lead_id: str, state: WorkflowState) -> FT:
    caps: list[dict[str, Any]] = []
    error = ""
    try:
        caps = await GatewayClient().list_capabilities()
    except Exception as exc:
        error = str(exc)
    return capability_picker(
        lead_id,
        caps,
        state.validation,
        smoke=state.validation.last_smoke_result,
        error=error,
    )


async def _validate_step(
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
    store: LeadStore,
) -> FT:
    report = validation_ui_service.load_report(lead_id)
    parts: list[FT] = []
    if report:
        parts.append(validation_results(lead_id, report))

    state = wizard.get_state(lead_id)
    if state.active_jobs.validate_job:
        job = jobs.get_job(lead_id, state.active_jobs.validate_job)
        parts.append(job_progress(job))
        parts.append(deploy_log_viewer(lead_id, job, jobs.tail_log(lead_id, job.job_id)))

    auth = f"headers:{{'Authorization':'Bearer {settings.internal_api_key}'}}"
    parts.append(
        Button(
            "Run full validation",
            cls=ButtonT.primary,
            hx_post=f"/api/leads/{lead_id}/validate",
            hx_target="#step-content",
            hx_swap="innerHTML",
            hx_headers=auth,
        )
    )
    return Div(*parts)


def _manual_cc_step(lead_id: str) -> FT:
    report = validation_ui_service.ensure_manual_checks(lead_id)
    return manual_checklist(
        lead_id,
        report.get("manual_control_centre_checks", []),
        settings.control_centre_base_url,
    )


def _cp3_step(lead_id: str, store: LeadStore) -> FT:
    report = validation_ui_service.load_report(lead_id)
    status = (report or {}).get("status", "pending")
    return _auth_form(
        lead_id,
        "cp3_approve",
        Alert(f"Validation status: {status}", cls=AlertT.info),
        LabelInput("Approver", name="actor", value="lead@example.com"),
        LabelTextArea("Notes", name="notes"),
    )


def _ship_prep(lead_id: str, store: LeadStore) -> FT:
    report = store.get_assessment_report(lead_id)
    rec = (report or {}).get("recommendation", {})
    return _auth_form(
        lead_id,
        "ship_prep",
        P("Review production deployment mapping before handover."),
        Ul(
            Li(f"Recommended pack: {rec.get('recommended_pack', 'n/a')}"),
            Li(f"Deployment target: internal assessment responses"),
        ),
    )


def _cp4_step(lead_id: str, store: LeadStore) -> FT:
    return _auth_form(
        lead_id,
        "cp4_approve",
        P("Final handover approval."),
        LabelInput("Approver", name="actor", value="client@example.com"),
        LabelTextArea("Notes", name="notes"),
    )


def _export_step(lead_id: str) -> FT:
    return _auth_form(
        lead_id,
        "export",
        P("Export pipeline CSV for CRM integration."),
        A("Go to export page", href="/export", cls="text-blue-600 underline"),
    )
