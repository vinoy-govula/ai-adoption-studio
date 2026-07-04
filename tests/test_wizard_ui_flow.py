from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fasthtml.common import to_xml
from httpx import ASGITransport, AsyncClient
from starlette.datastructures import FormData

from ai_adoption_studio.components.cursor_assist_panel import cursor_assist_panel
from ai_adoption_studio.components.goal_banner import goal_banner
from ai_adoption_studio.components.htmx import operator_hx_headers
from ai_adoption_studio.layouts.base import theme_headers
from ai_adoption_studio.layouts.base import wizard_layout
from ai_adoption_studio.main import _form_to_dict, app
from ai_adoption_studio.models.certification_verdict import CertificationVerdict, EvidenceItem
from ai_adoption_studio.models.job_record import JobStatus
from ai_adoption_studio.models.workflow_state import STEP_ORDER, StepStatus
from ai_adoption_studio.pages.wizard import handle_step_post
from ai_adoption_studio.pages.wizard_steps.render import render_step
from ai_adoption_studio.services.job_runner import JobRunner
from ai_adoption_studio.services.store import LeadStore
from ai_adoption_studio.services.validation_ui_service import MANUAL_CHECK_IDS
from ai_adoption_studio.services.wizard_service import WizardService


@pytest.fixture
def store(tmp_path: Path) -> LeadStore:
    return LeadStore(tmp_path)


@pytest.fixture
def lead_id(store: LeadStore) -> str:
    record = store.create_eoi(
        {
            "consent": {"privacy_policy_accepted": True, "contact_permitted": True},
            "responses": {
                "org_name": "Mock Org",
                "industry": "healthcare",
                "contact_email": "sponsor@example.com",
                "contact_name": "Sponsor",
                "intent": "deploy",
                "use_case_interest": ["knowledge_assistant"],
            },
        }
    )
    return record["lead_id"]


@pytest.fixture
def wizard(store: LeadStore) -> WizardService:
    return WizardService(store)


@pytest.fixture
def jobs(store: LeadStore, wizard: WizardService) -> JobRunner:
    return JobRunner(store, wizard)


@pytest.fixture(autouse=True)
def isolate_validation_services(store: LeadStore, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ai_adoption_studio.pages.wizard.validation_ui_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.pages.wizard_steps.render.validation_ui_service._store", store)


def _internal_responses() -> dict[str, Any]:
    return {
        "executive_sponsor_identified": "true",
        "ai_strategy_documented": "draft",
        "document_corpus_ready": "partially_curated",
        "data_classification_in_place": "true",
        "compliance_frameworks": "privacy_act",
        "audit_retention_requirement": "90_days",
        "it_ops_capacity": "moderate",
        "deployment_target": "private_cloud",
        "concurrent_users": "25",
        "daily_requests": "8000",
        "target_latency_ms": "3000",
        "change_champion_identified": "true",
        "staff_ai_literacy": "moderate",
    }


def _deployment_report(status: str = "passed") -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "status": status,
        "summary": {"checks_total": 1, "checks_passed": 1 if status == "passed" else 0},
        "checks": [{"id": "mock_check", "status": status, "message": "mocked"}],
        "manual_control_centre_checks": [
            {"id": check_id, "status": "pending", "notes": ""} for check_id in MANUAL_CHECK_IDS
        ],
    }


def _write_deployment_report(store: LeadStore, lead_id: str, status: str = "passed") -> None:
    path = store._store.lead_dir(lead_id) / "deployment-report.json"
    path.write_text(json.dumps(_deployment_report(status), indent=2), encoding="utf-8")


def _hx_header_values(html: str) -> list[dict[str, str]]:
    values = []
    for _, raw in re.findall(r"hx-headers=(['\"])(.*?)\1", html):
        values.append(json.loads(unescape(raw)))
    return values


def test_operator_hx_headers_are_valid_json() -> None:
    assert json.loads(operator_hx_headers()) == {"Authorization": "Bearer dev-key"}


def test_step_nav_preserves_buttons_when_saving_draft() -> None:
    from ai_adoption_studio.components.nav_buttons import step_nav

    html = to_xml(step_nav("lead-1", "assessment_form"))

    assert 'hx-target="#wizard-notify-msg"' in html
    assert 'id="wizard-notify-msg"' in html
    assert "Save draft" in html
    assert "Next" in html


def test_cursor_assist_buttons_have_click_state() -> None:
    html = to_xml(cursor_assist_panel("lead-1"))

    assert "Certify deployment" in html
    assert 'type="button"' in html
    assert "uk-btn uk-btn-primary" in html
    assert "min-w-44 h-10 inline-flex items-center justify-center text-center" in html
    assert 'data-cursor-assist-action="certify"' in html
    assert 'data-cursor-assist-action="pir"' in html
    assert "setAttribute('aria-pressed','true')" in html
    assert "classList.add('uk-btn-primary')" in html


def test_goal_banner_stays_sticky_on_scroll() -> None:
    html = to_xml(goal_banner("assessment_run"))

    assert "Run assessment" in html
    assert "sticky top-0 z-20" in html


def test_theme_headers_load_core_htmx_before_extensions() -> None:
    html = "".join(to_xml(header) for header in theme_headers())

    core = "htmx.org"
    sse = "htmx-ext-sse"
    assert core in html
    assert sse in html
    assert html.index(core) < html.index(sse)


def test_wizard_layout_keeps_stepper_fixed() -> None:
    html = to_xml(wizard_layout("Wizard", "lead-1", "steps", "content", org_name="Mock Org"))

    assert 'id="wizard-stepper"' in html
    assert 'class="fixed inset-y-0 left-0 z-10 w-56"' in html
    assert 'class="flex-1 p-6 ml-56"' in html


def test_form_to_dict_preserves_repeated_form_values() -> None:
    form = FormData([("tags", "x"), ("tags", "y"), ("name", "Mock")])

    assert _form_to_dict(form) == {"tags": ["x", "y"], "name": "Mock"}


@pytest.mark.asyncio
async def test_htmx_step_get_returns_partial_with_refreshed_stepper(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.services.wizard_service.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._wizard._store", store)

    wizard.ensure_state(lead_id)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer dev-key", "HX-Request": "true"},
    ) as client:
        response = await client.get(f"/wizard/{lead_id}/eoi_review")

    assert response.status_code == 200
    assert "<html" not in response.text.lower()
    assert 'id="step-form-eoi_review"' in response.text
    assert 'id="wizard-stepper"' in response.text
    assert 'class="fixed inset-y-0 left-0 z-10 w-56"' in response.text
    assert "hx-swap-oob" in response.text


@pytest.mark.asyncio
async def test_htmx_step_post_advances_content_and_refreshes_stepper(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.services.wizard_service.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._wizard._store", store)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer dev-key", "HX-Request": "true"},
    ) as client:
        response = await client.post(
            f"/wizard/{lead_id}/eoi_review",
            data={"acknowledged": "true"},
        )

    assert response.status_code == 200
    assert "<html" not in response.text.lower()
    assert 'id="step-form-qualify"' in response.text
    assert 'id="wizard-stepper"' in response.text
    assert "hx-swap-oob" in response.text


@pytest.mark.asyncio
async def test_save_draft_route_is_not_captured_as_step(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.services.wizard_service.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main.wizard_service._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._store", store)
    monkeypatch.setattr("ai_adoption_studio.main._jobs._wizard._store", store)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer dev-key", "HX-Request": "true"},
    ) as client:
        response = await client.post(
            f"/wizard/{lead_id}/draft",
            data={"step_id": "assessment_form", "ai_strategy_documented": "draft"},
        )

    assert response.status_code == 200
    assert "Draft saved." in response.text
    state = wizard.get_state(lead_id)
    assert state.draft_payloads["assessment_form"]["ai_strategy_documented"] == "draft"


@pytest.mark.asyncio
async def test_all_wizard_steps_render_valid_authenticated_next_forms(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_adoption_studio.services.status_aggregator import LayerStatus, StatusSnapshot

    monkeypatch.setattr(
        "ai_adoption_studio.pages.wizard_steps.render.GatewayClient.list_capabilities",
        AsyncMock(return_value=[{"capability_id": "chat", "name": "Chat"}]),
    )
    monkeypatch.setattr(
        "ai_adoption_studio.pages.wizard_steps.render.status_aggregator.poll",
        AsyncMock(
            return_value=StatusSnapshot(
                overall="healthy",
                layers={"gateway": LayerStatus(status="healthy", summary="OK")},
            )
        ),
    )

    wizard.ensure_state(lead_id)

    for step_id in STEP_ORDER:
        html = to_xml(
            await render_step(lead_id, step_id, store=store, wizard=wizard, jobs=jobs)
        )

        assert f'id="step-form-{step_id}"' in html
        assert f'hx-post="/wizard/{lead_id}/{step_id}"' in html
        assert f'hx-include="#step-form-{step_id}"' in html
        assert 'type="button"' in html
        assert "headers:" not in html

        header_values = _hx_header_values(html)
        assert header_values
        assert all(value == {"Authorization": "Bearer dev-key"} for value in header_values)


@pytest.mark.asyncio
async def test_eoi_review_renders_edit_link_and_customer_guidance(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    wizard.ensure_state(lead_id)

    html = to_xml(await render_step(lead_id, "eoi_review", store=store, wizard=wizard, jobs=jobs))

    assert "Edit EOI" in html
    assert f'href="/eoi/{lead_id}"' in html
    assert "Review these details with the customer" in html


@pytest.mark.asyncio
async def test_branding_step_renders_field_help(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    wizard.ensure_state(lead_id)

    html = to_xml(await render_step(lead_id, "branding_kit", store=store, wizard=wizard, jobs=jobs))

    assert "Help me choose" in html
    assert "Client slug" in html
    assert "Common values: 7, 14, 30." in html


@pytest.mark.asyncio
async def test_deploy_step_explains_prerequisites(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    wizard.ensure_state(lead_id)

    html = to_xml(await render_step(lead_id, "deploy_lab", store=store, wizard=wizard, jobs=jobs))

    assert "CP2 client approval recorded" in html
    assert "Confirms the customer has approved the assessment" in html
    assert "Playground manifest exists" in html
    assert "deployment manifest used by the delivery validator" in html
    assert "Platform API key configured" in html
    assert "Set STUDIO_PLATFORM_API_KEY" in html
    assert "Gateway health endpoint reachable" in html
    assert "Control Centre health endpoint reachable" in html
    assert "How to resolve:" in html
    assert "Start deploy" in html
    assert "Starting deploy..." in html
    assert "Creating deployment job. Progress and logs will appear below." in html


@pytest.mark.asyncio
async def test_deploy_step_shows_active_job_progress(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    wizard.ensure_state(lead_id)
    job = jobs.create_job(lead_id, "deploy")
    job.status = JobStatus.RUNNING
    job.progress_pct = 25
    job.message = "Deploying lab stack via delivery validator."
    jobs.update_job(lead_id, job)
    log_path = jobs._log_path(lead_id, job.job_id)
    log_path.write_text("INFO starting\nERROR docker compose failed\n", encoding="utf-8")
    wizard.set_active_job(lead_id, "deploy", job.job_id)

    html = to_xml(await render_step(lead_id, "deploy_lab", store=store, wizard=wizard, jobs=jobs))

    assert f"Deployment job {job.job_id} is running" in html
    assert "This panel refreshes automatically while the job runs." in html
    assert "Deployment progress" in html
    assert "Deploying lab stack via delivery validator." in html
    assert "25% complete" in html
    assert "Refresh terminal" in html
    assert "Download log" in html
    assert "Diagnose with Cursor" in html
    assert "Failure intelligence" in html
    assert "Deployment terminal" in html
    assert "ERROR docker compose failed" in html
    assert f'hx-target="#job-diagnosis-{job.job_id}"' in html
    assert f'hx-target="#job-progress-{job.job_id}"' in html
    assert "uk-btn uk-btn-secondary" in html
    assert "Start deploy" not in html


@pytest.mark.asyncio
async def test_cursor_certify_response_explains_verdict(
    store: LeadStore,
    lead_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ai_adoption_studio.services.store.lead_store", store)
    monkeypatch.setattr("ai_adoption_studio.main.lead_store", store)
    monkeypatch.setattr(
        "ai_adoption_studio.services.certification_service.CertificationService.certify",
        AsyncMock(
            return_value=CertificationVerdict(
                verdict="conditional",
                confidence=0.6,
                conditions=["Complete validation and manual CC checklist"],
                evidence=[EvidenceItem(source="manifest", finding="Manifest generated")],
                recommended_actions=["Run full validation"],
            )
        ),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer dev-key"},
    ) as client:
        response = await client.post(f"/api/leads/{lead_id}/cursor/certify")

    assert response.status_code == 200
    assert "The deployment can continue" in response.text
    assert "Confidence reflects" in response.text
    assert "Conditions to clear" in response.text
    assert "Evidence reviewed" in response.text
    assert "manifest: Manifest generated" in response.text
    assert "Recommended actions" in response.text


def test_locked_steps_unlock_when_artifacts_appear(store: LeadStore, lead_id: str, wizard: WizardService) -> None:
    state = wizard.ensure_state(lead_id)
    assert state.steps["assessment_run"].status == StepStatus.LOCKED

    store.save_internal_responses(lead_id, _internal_responses())

    state = wizard.get_state(lead_id)
    assert state.steps["assessment_run"].status in {StepStatus.AVAILABLE, StepStatus.IN_PROGRESS}


@pytest.mark.asyncio
async def test_eoi_review_requires_acknowledgement_before_progressing(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    wizard.ensure_state(lead_id)

    html = to_xml(
        await handle_step_post(lead_id, "eoi_review", {}, store=store, wizard=wizard, jobs=jobs)
    )

    state = wizard.get_state(lead_id)
    assert state.current_step == "eoi_review"
    assert state.steps["eoi_review"].status == StepStatus.IN_PROGRESS
    assert "Acknowledge EOI to continue." in html


@pytest.mark.asyncio
async def test_questionnaire_validation_blocks_invalid_data_and_preserves_state(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    wizard.advance(lead_id, "eoi_review")
    wizard.advance(lead_id, "qualify")

    html = to_xml(
        await handle_step_post(
            lead_id,
            "assessment_form",
            {"concurrent_users": "0", "daily_requests": "not-an-int"},
            store=store,
            wizard=wizard,
            jobs=jobs,
        )
    )

    state = wizard.get_state(lead_id)
    assert state.current_step == "assessment_form"
    assert store.get_internal_responses(lead_id) is None
    assert "This field is required." in html
    assert "Must be an integer." in html


@pytest.mark.asyncio
async def test_questionnaire_success_saves_coerced_data_and_advances(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    wizard.advance(lead_id, "eoi_review")
    wizard.advance(lead_id, "qualify")

    await handle_step_post(
        lead_id,
        "assessment_form",
        _internal_responses(),
        store=store,
        wizard=wizard,
        jobs=jobs,
    )

    state = wizard.get_state(lead_id)
    saved = store.get_internal_responses(lead_id)
    assert state.current_step == "assessment_run"
    assert saved is not None
    assert saved["concurrent_users"] == 25
    assert saved["executive_sponsor_identified"] is True


@pytest.mark.asyncio
async def test_action_steps_block_next_until_required_work_is_done(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_adoption_studio.services.status_aggregator import StatusSnapshot

    monkeypatch.setattr(
        "ai_adoption_studio.pages.wizard_steps.render.status_aggregator.poll",
        AsyncMock(return_value=StatusSnapshot(overall="unknown")),
    )

    deploy_html = to_xml(
        await handle_step_post(lead_id, "deploy_lab", {}, store=store, wizard=wizard, jobs=jobs)
    )
    assert "Start deploy before continuing." in deploy_html
    assert wizard.get_state(lead_id).current_step != "live_status"

    live_html = to_xml(
        await handle_step_post(lead_id, "live_status", {}, store=store, wizard=wizard, jobs=jobs)
    )
    assert "Wait for the lab deployment to become active before continuing." in live_html
    assert wizard.get_state(lead_id).current_step != "llm_test_select"

    validate_html = to_xml(
        await handle_step_post(lead_id, "validate", {}, store=store, wizard=wizard, jobs=jobs)
    )
    assert "Run full validation before continuing." in validate_html
    assert wizard.get_state(lead_id).current_step != "manual_cc"


@pytest.mark.asyncio
async def test_manual_control_centre_checklist_requires_all_checks(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    _write_deployment_report(store, lead_id, status="passed")

    incomplete_html = to_xml(
        await handle_step_post(lead_id, "manual_cc", {}, store=store, wizard=wizard, jobs=jobs)
    )
    assert "Complete Control Centre checks before continuing." in incomplete_html
    assert wizard.get_state(lead_id).current_step != "cp3_approve"

    complete_form = {check_id: "complete" for check_id in MANUAL_CHECK_IDS}
    await handle_step_post(lead_id, "manual_cc", complete_form, store=store, wizard=wizard, jobs=jobs)

    state = wizard.get_state(lead_id)
    assert state.cp3_checklist_complete is True
    assert state.current_step == "cp3_approve"


@pytest.mark.asyncio
async def test_cp3_approval_requires_passed_validation_and_completed_checklist(
    store: LeadStore,
    lead_id: str,
    wizard: WizardService,
    jobs: JobRunner,
) -> None:
    _write_deployment_report(store, lead_id, status="failed")
    wizard.set_checklist_complete(lead_id, True)

    failed_validation_html = to_xml(
        await handle_step_post(
            lead_id,
            "cp3_approve",
            {"actor": "lead@example.com"},
            store=store,
            wizard=wizard,
            jobs=jobs,
        )
    )
    assert "Validation must pass before lab sign-off." in failed_validation_html

    _write_deployment_report(store, lead_id, status="passed")
    wizard.set_checklist_complete(lead_id, False)

    incomplete_checklist_html = to_xml(
        await handle_step_post(
            lead_id,
            "cp3_approve",
            {"actor": "lead@example.com"},
            store=store,
            wizard=wizard,
            jobs=jobs,
        )
    )
    assert "Complete Control Centre checks before lab sign-off." in incomplete_checklist_html
