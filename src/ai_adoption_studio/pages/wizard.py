"""Wizard shell and step action handlers."""

from __future__ import annotations

import json
from typing import Any

from fasthtml.common import Div, FT
from fasthtml.common import *  # noqa: F403

from ai_adoption_studio.components.stepper import wizard_stepper
from ai_adoption_studio.layouts.base import wizard_layout
from ai_adoption_studio.models.workflow_state import STEP_ORDER
from ai_adoption_studio.pages.wizard_steps.render import render_step
from ai_adoption_studio.services.assessment_service import (
    approve_assessment_checkpoint,
    qualify_lead,
    regenerate_narrative,
    run_assessment,
)
from ai_adoption_studio.services.form_validator import form_validator
from ai_adoption_studio.services.job_runner import JobRunner
from ai_adoption_studio.services.question_set_loader import question_set_loader
from ai_adoption_studio.services.store import LeadStore
from ai_adoption_studio.services.validation_ui_service import validation_ui_service
from ai_adoption_studio.services.wizard_service import WizardService
from ai_runtime_manager.assessment.checkpoints import approve_checkpoint


async def wizard_page(
    lead_id: str,
    step_id: str | None,
    *,
    store: LeadStore,
    wizard: WizardService,
    jobs: JobRunner,
    message: str = "",
) -> FT:
    state = wizard.ensure_state(lead_id)
    current = step_id or state.current_step
    if current not in STEP_ORDER:
        current = state.current_step
    try:
        wizard.goto_step(lead_id, current)
        state = wizard.get_state(lead_id)
    except ValueError:
        current = state.current_step

    eoi = store.get_eoi(lead_id)
    org = eoi.get("responses", {}).get("org_name", lead_id)
    stepper = wizard_stepper(lead_id, state.step_meta(), current)
    content = await render_step(lead_id, current, store=store, wizard=wizard, jobs=jobs, message=message)
    return wizard_layout(f"Wizard — {org}", lead_id, stepper, content, org_name=org)


async def wizard_step_partial(
    lead_id: str,
    step_id: str | None,
    *,
    store: LeadStore,
    wizard: WizardService,
    jobs: JobRunner,
    message: str = "",
    errors: dict[str, list[str]] | None = None,
    include_stepper: bool = False,
) -> FT:
    state = wizard.ensure_state(lead_id)
    current = step_id or state.current_step
    if current not in STEP_ORDER:
        current = state.current_step
    try:
        wizard.goto_step(lead_id, current)
        state = wizard.get_state(lead_id)
    except ValueError:
        current = state.current_step

    content = await render_step(
        lead_id,
        current,
        store=store,
        wizard=wizard,
        jobs=jobs,
        message=message,
        errors=errors,
    )
    if not include_stepper:
        return content

    stepper = wizard_stepper(lead_id, state.step_meta(), current)
    return Div(
        content,
        Div(
            stepper,
            id="wizard-stepper",
            cls="fixed inset-y-0 left-0 z-10 w-56",
            hx_swap_oob="outerHTML",
        ),
    )


async def handle_step_post(
    lead_id: str,
    step_id: str,
    form: dict[str, Any],
    *,
    store: LeadStore,
    wizard: WizardService,
    jobs: JobRunner,
    include_stepper: bool = False,
) -> FT:
    message = ""
    errors: dict[str, list[str]] | None = None

    async def _render(
        current_step: str,
        *,
        message: str = "",
        errors: dict[str, list[str]] | None = None,
    ) -> FT:
        return await wizard_step_partial(
            lead_id,
            current_step,
            store=store,
            wizard=wizard,
            jobs=jobs,
            message=message,
            errors=errors,
            include_stepper=include_stepper,
        )

    if step_id == "eoi_review":
        if form.get("acknowledged") != "true":
            return await _render(step_id, message="Acknowledge EOI to continue.")
        wizard.advance(lead_id, step_id)

    elif step_id == "qualify":
        actor = form.get("actor", "sales")
        qualify_lead(store, lead_id, actor=actor)
        wizard.advance(lead_id, step_id, actor=actor)

    elif step_id == "assessment_form":
        qs = question_set_loader.get_internal()
        raw = {k: v for k, v in form.items() if k not in {"step_id"}}
        errors = form_validator.validate(qs, raw)
        if errors:
            return await _render(step_id, errors=errors)
        internal = form_validator.coerce(qs, raw)
        store.save_internal_responses(lead_id, internal)
        wizard.advance(lead_id, step_id)

    elif step_id == "assessment_run":
        internal = store.get_internal_responses(lead_id)
        if not internal:
            return await _render(step_id, message="Complete questionnaire first.")
        await run_assessment(store, lead_id, internal)
        wizard.advance(lead_id, step_id)

    elif step_id == "narrative":
        if form.get("regenerate") == "true":
            await regenerate_narrative(store, lead_id, use_llm=False)
        else:
            report = store.get_assessment_report(lead_id)
            if report:
                await regenerate_narrative(store, lead_id, use_llm=False)
        wizard.advance(lead_id, step_id)

    elif step_id == "cp2_approve":
        actor = form.get("actor", "client@example.com")
        notes = form.get("notes", "")
        approve_assessment_checkpoint(store, lead_id, actor=actor, notes=notes)
        wizard.advance(lead_id, step_id, actor=actor)

    elif step_id == "branding_kit":
        branding = {
            "client_slug": form.get("client_slug", ""),
            "display_name": form.get("display_name", ""),
            "welcome_message": form.get("welcome_message", ""),
            "logo_url": form.get("logo_url", ""),
            "public_url": form.get("public_url", ""),
            "ttl_days": int(form.get("ttl_days", 30) or 30),
            "infrastructure_stage": form.get("infrastructure_stage", "playground"),
            "use_edge_overlay": form.get("use_edge_overlay") == "true",
            "playground_preset_key": form.get("playground_preset_key", ""),
            "production_model": form.get("production_model", ""),
            "model_selection_source": "operator",
        }
        if not branding["playground_preset_key"] or not branding["production_model"]:
            return await _render(
                step_id,
                message="Select both a certified playground preset and production model before generating the manifest.",
            )
        wizard.save_branding(lead_id, branding)
        lead_dir = store._store.lead_dir(lead_id)
        branding_path = lead_dir / "branding.json"
        branding_path.write_text(json.dumps(branding, indent=2), encoding="utf-8")

        from ai_adoption_studio.config import settings as studio_settings

        if studio_settings.enterprise_delivery_enabled:
            from ai_adoption_studio.adapters.delivery_validator import DeploymentOrchestrator

            assessment_path = lead_dir / "assessment-report.json"
            orchestrator = DeploymentOrchestrator()
            try:
                await orchestrator.generate_kit(
                    lead_id,
                    assessment_path,
                    branding,
                    lead_dir,
                    log_path=lead_dir / "jobs" / "kit-generate.log",
                )
                message = "Manifest generated."
            except Exception as exc:
                return await _render(step_id, message=str(exc))
        else:
            from ai_adoption_studio.services.client_yaml_export import export_client_yaml

            path = export_client_yaml(lead_id=lead_id, store=store, branding=branding)
            message = f"client.yaml exported to {path.name}. Run package-builder in deployment-catalog."
        wizard.advance(lead_id, step_id)

    elif step_id == "deploy_lab":
        from ai_adoption_studio.config import settings as studio_settings

        if not studio_settings.enterprise_delivery_enabled:
            wizard.advance(lead_id, step_id)
            return await _render(step_id, message="Skipped — use package-builder for single-config delivery.")
        if not wizard._manifest_active(lead_id):
            return await _render(step_id, message="Start deploy before continuing.")
        wizard.advance(lead_id, step_id)

    elif step_id == "live_status":
        if not wizard._manifest_active(lead_id):
            return await _render(
                step_id,
                message="Wait for the lab deployment to become active before continuing.",
            )
        wizard.advance(lead_id, step_id)

    elif step_id == "llm_test_select":
        wizard.update_validation(
            lead_id,
            test_capability=form.get("test_capability", "chat"),
            test_prompt=form.get("test_prompt", ""),
            selection_source="operator",
        )
        manifest_path = store._store.lead_dir(lead_id) / "playground-kit.manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.setdefault("validation", {})
            manifest["validation"]["test_capability"] = form.get("test_capability", "chat")
            manifest["validation"]["test_prompt"] = form.get("test_prompt", "")
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        wizard.advance(lead_id, step_id)

    elif step_id == "validate":
        from ai_adoption_studio.config import settings as studio_settings

        if not studio_settings.enterprise_delivery_enabled:
            wizard.advance(lead_id, step_id)
            return await _render(step_id, message="Skipped — use platform-smoke-test on the deployment package.")
        if not validation_ui_service.load_report(lead_id):
            return await _render(step_id, message="Run full validation before continuing.")
        wizard.advance(lead_id, step_id)

    elif step_id == "manual_cc":
        report = validation_ui_service.ensure_manual_checks(lead_id)
        checks = []
        for item in report.get("manual_control_centre_checks", []):
            cid = item["id"]
            status = "complete" if form.get(cid) == "complete" else "pending"
            checks.append({"id": cid, "status": status, "notes": form.get(f"{cid}_notes", "")})
        validation_ui_service.save_manual_checks(lead_id, checks)
        complete = validation_ui_service.checklist_complete(lead_id)
        wizard.set_checklist_complete(lead_id, complete)
        if not complete:
            return await _render(
                step_id,
                message="Complete Control Centre checks before continuing.",
            )
        wizard.advance(lead_id, step_id)

    elif step_id == "cp3_approve":
        deployment_report = validation_ui_service.load_report(lead_id)
        state = wizard.get_state(lead_id)
        if not deployment_report or deployment_report.get("status") != "passed":
            return await _render(step_id, message="Validation must pass before lab sign-off.")
        if not state.cp3_checklist_complete:
            return await _render(
                step_id,
                message="Complete Control Centre checks before lab sign-off.",
            )
        report = store.get_assessment_report(lead_id)
        if report:
            updated = approve_checkpoint(
                report,
                "cp3_deploy_test_approved",
                actor=form.get("actor", "lead@example.com"),
                notes=form.get("notes", ""),
            )
            store.save_assessment_report(lead_id, updated)
        wizard.advance(lead_id, step_id)

    elif step_id == "ship_prep":
        ship_prep = {
            "production_edge": form.get("production_edge", "customer-managed"),
            "routing_model": form.get("routing_model", "path-based"),
            "reference_configs_delivered": form.get("reference_configs_delivered") == "true",
            "customer_edge_owner_identified": form.get("customer_edge_owner_identified") == "true",
            "notes": form.get("notes", ""),
        }
        wizard.save_ship_prep(lead_id, ship_prep)
        lead_dir = store._store.lead_dir(lead_id)
        manifest_path = lead_dir / "playground-kit.manifest.json"
        if manifest_path.exists():
            from ai_adoption_studio.services.ship_prep import write_nginx_reference

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            write_nginx_reference(lead_dir, manifest)
        wizard.advance(lead_id, step_id)

    elif step_id == "cp4_approve":
        report = store.get_assessment_report(lead_id)
        if report:
            updated = approve_checkpoint(
                report,
                "cp4_ship_approved",
                actor=form.get("actor", "client@example.com"),
                notes=form.get("notes", ""),
            )
            store.save_assessment_report(lead_id, updated)
        wizard.advance(lead_id, step_id)

    elif step_id == "export":
        wizard.advance(lead_id, step_id)

    else:
        wizard.advance(lead_id, step_id)

    state = wizard.get_state(lead_id)
    return await _render(state.current_step, message=message)
