import logging
from pathlib import Path

from fasthtml.common import fast_app

from ai_adoption_studio import __version__
from ai_adoption_studio.api.eoi import register_eoi_routes
from ai_adoption_studio.config import settings
from ai_adoption_studio.pages.studio import assessment_page, eoi_form_page, export_page, leads_page
from ai_adoption_studio.services.assessment_service import (
    approve_assessment_checkpoint,
    export_csv,
    qualify_lead,
    regenerate_narrative,
    run_assessment,
)
from ai_adoption_studio.services.store import lead_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app, rt = fast_app()
register_eoi_routes(app)


@rt("/")
def leads_index():
    return leads_page(lead_store.list_leads())


@rt("/leads/{lead_id}")
def lead_detail(lead_id: str):
    eoi = lead_store.get_eoi(lead_id)
    report = lead_store.get_assessment_report(lead_id)
    narrative = lead_store._store.lead_dir(lead_id) / (report or {}).get(
        "llm_narrative_ref",
        "",
    )
    narrative_path = str(narrative) if narrative.exists() else None
    return assessment_page(lead_id, eoi, report, narrative_path)


@rt("/leads/{lead_id}/assess", methods=["POST"])
async def lead_assess(
    lead_id: str,
    concurrent_users: int = 25,
    daily_requests: int = 8000,
    it_ops_capacity: str = "moderate",
    deployment_target: str = "private_cloud",
    executive_sponsor_identified: str = "",
):
    internal = {
        "executive_sponsor_identified": executive_sponsor_identified == "true",
        "ai_strategy_documented": "draft",
        "document_corpus_ready": "partially_curated",
        "data_classification_in_place": True,
        "compliance_frameworks": ["privacy_act"],
        "audit_retention_requirement": "90_days",
        "it_ops_capacity": it_ops_capacity,
        "deployment_target": deployment_target,
        "concurrent_users": concurrent_users,
        "daily_requests": daily_requests,
        "change_champion_identified": True,
        "staff_ai_literacy": "moderate",
    }
    await run_assessment(lead_store, lead_id, internal)
    return lead_detail(lead_id)


@rt("/leads/{lead_id}/qualify", methods=["POST"])
def lead_qualify(lead_id: str):
    qualify_lead(lead_store, lead_id, actor="sales")
    return leads_page(lead_store.list_leads(), message=f"Lead {lead_id} qualified.")


@rt("/leads/{lead_id}/approve-cp2", methods=["POST"])
def lead_approve_cp2(lead_id: str, actor: str = "client@example.com"):
    approve_assessment_checkpoint(lead_store, lead_id, actor=actor)
    return lead_detail(lead_id)


@rt("/leads/{lead_id}/narrative", methods=["POST"])
async def lead_narrative(lead_id: str):
    await regenerate_narrative(lead_store, lead_id, use_llm=False)
    return lead_detail(lead_id)


@rt("/export")
def export_view():
    export_dir = settings.data_root / "exports"
    files = [path.name for path in export_dir.glob("*")] if export_dir.exists() else []
    return export_page(files)


@rt("/export", methods=["POST"])
def export_run():
    export_dir = settings.data_root / "exports"
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
