"""Application entrypoint — FastHTML + MonsterUI operator wizard."""

from __future__ import annotations

import logging

from fasthtml.common import fast_app
from starlette.requests import Request
from starlette.responses import RedirectResponse

from ai_adoption_studio import __version__
from ai_adoption_studio.adapters.cursor_agent import CursorAgentBridge
from ai_adoption_studio.api.eoi import register_eoi_routes
from ai_adoption_studio.config import settings
from ai_adoption_studio.layouts.base import theme_headers
from ai_adoption_studio.middleware.auth import InternalAuthMiddleware
from ai_adoption_studio.pages.inbox import inbox_page
from ai_adoption_studio.pages.studio import export_page, eoi_form_page
from ai_adoption_studio.pages.wizard import handle_step_post, wizard_page
from ai_adoption_studio.routes.api_cursor import register_api_cursor_routes
from ai_adoption_studio.routes.api_jobs import register_api_job_routes
from ai_adoption_studio.routes.api_leads import register_api_lead_routes
from ai_adoption_studio.services.assessment_service import export_csv
from ai_adoption_studio.services.certification_service import CertificationService
from ai_adoption_studio.services.job_runner import JobRunner
from ai_adoption_studio.services.smoke_test_service import SmokeTestService
from ai_adoption_studio.services.store import LeadStore, lead_store
from ai_adoption_studio.services.wizard_service import WizardService, wizard_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app, rt = fast_app(hdrs=theme_headers())
app.add_middleware(InternalAuthMiddleware)

_jobs = JobRunner(lead_store, wizard_service)
_smoke = SmokeTestService(wizard_service)
_bridge = CursorAgentBridge(lead_store)
_certify = CertificationService(wizard_service, _bridge)

register_eoi_routes(app)
register_api_lead_routes(app, lead_store, wizard_service, _jobs, _smoke)
register_api_job_routes(app, lead_store, _jobs)
register_api_cursor_routes(app, lead_store, _bridge, _certify)


@rt("/")
def inbox_index():
    return inbox_page(lead_store.list_leads())


@rt("/wizard/{lead_id}", methods=["GET"])
async def wizard_entry(lead_id: str):
    return await wizard_page(lead_id, None, store=lead_store, wizard=wizard_service, jobs=_jobs)


@rt("/wizard/{lead_id}/{step_id}", methods=["GET"])
async def wizard_step_get(lead_id: str, step_id: str):
    return await wizard_page(lead_id, step_id, store=lead_store, wizard=wizard_service, jobs=_jobs)


@rt("/wizard/{lead_id}/{step_id}", methods=["POST"])
async def wizard_step_post(lead_id: str, step_id: str, req: Request):
    form = dict(await req.form())
    return await handle_step_post(lead_id, step_id, form, store=lead_store, wizard=wizard_service, jobs=_jobs)


@rt("/wizard/{lead_id}/back", methods=["POST"])
async def wizard_back(lead_id: str, req: Request):
    form = dict(await req.form())
    step_id = str(form.get("step_id", ""))
    wizard_service.go_back(lead_id, step_id or None)
    state = wizard_service.get_state(lead_id)
    from ai_adoption_studio.pages.wizard_steps.render import render_step

    return await render_step(lead_id, state.current_step, store=lead_store, wizard=wizard_service, jobs=_jobs)


@rt("/wizard/{lead_id}/draft", methods=["POST"])
async def wizard_draft(lead_id: str, req: Request):
    form = dict(await req.form())
    step_id = str(form.get("step_id", ""))
    wizard_service.save_draft(lead_id, step_id, form)
    from fasthtml.common import P

    return P("Draft saved.", cls="text-green-700 text-sm")


@rt("/leads/{lead_id}")
def legacy_lead_redirect(lead_id: str):
    return RedirectResponse(url=f"/wizard/{lead_id}", status_code=302)


@rt("/export")
def export_view():
    export_dir = settings.data_root / "exports"
    files = [path.name for path in export_dir.glob("*")] if export_dir.exists() else []
    return export_page(files)


@rt("/export", methods=["POST"])
def export_run():
    export_dir = settings.data_root / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    written = export_csv(lead_store, export_dir, as_zip=True)
    return export_page([path.name for path in written], message="Export complete.")


@rt("/eoi-form")
def eoi_form():
    return eoi_form_page()


@rt("/eoi-form", methods=["POST"])
def eoi_form_submit(
    org_name: str,
    industry: str,
    contact_email: str,
    contact_name: str,
    intent: str,
    privacy_policy_accepted: str = "",
    contact_permitted: str = "",
):
    record = lead_store.create_eoi(
        {
            "source": "website",
            "consent": {
                "privacy_policy_accepted": privacy_policy_accepted == "true",
                "contact_permitted": contact_permitted == "true",
            },
            "responses": {
                "org_name": org_name,
                "industry": industry,
                "employee_band": "51-200",
                "country": "AU",
                "contact_name": contact_name,
                "contact_email": contact_email,
                "contact_role": "Sponsor",
                "intent": intent,
                "primary_pain": ["privacy_compliance"],
                "data_sensitivity": "medium",
                "data_residency_required": True,
                "user_band": "51-200",
                "use_case_interest": ["knowledge_assistant"],
                "timeline": "1-3_months",
                "gpu_available": "planned",
                "current_ai_usage": "none",
            },
        }
    )
    return eoi_form_page(message=f"EOI submitted: {record['lead_id']}")


@rt("/healthz")
def healthz():
    return {"status": "healthy", "service": "ai-adoption-studio", "version": __version__}
