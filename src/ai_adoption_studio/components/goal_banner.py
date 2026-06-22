"""Step goal banner."""

from __future__ import annotations

from fasthtml.common import *  # noqa: F403
from monsterui.all import *  # noqa: F403


STEP_GOALS: dict[str, tuple[str, str, str]] = {
    "eoi_review": ("Review submitted EOI", "Confirm lead details before qualification.", "5 min", "Sales"),
    "qualify": ("Qualify lead", "Mark lead as qualified for assessment.", "2 min", "Sales"),
    "assessment_form": ("Complete questionnaire", "Capture internal readiness signals.", "15 min", "Architect"),
    "assessment_run": ("Run assessment", "Execute rule engine and generate report.", "5 min", "Architect"),
    "narrative": ("Review narrative", "Preview client-facing assessment narrative.", "5 min", "Architect"),
    "cp2_approve": ("Client approval (cp2)", "Record client sign-off on assessment.", "5 min", "Client"),
    "branding_kit": ("Generate playground kit", "Configure branding and generate manifest.", "10 min", "Operator"),
    "deploy_lab": ("Deploy lab stack", "Deploy playground via delivery validator.", "20 min", "Operator"),
    "live_status": ("Monitor live status", "Verify Gateway, RM, CC health.", "5 min", "Operator"),
    "llm_test_select": ("Select test capability", "Choose capability for smoke and validation.", "5 min", "Operator"),
    "validate": ("Run validation", "Execute automated validation suite.", "15 min", "Operator"),
    "manual_cc": ("Control Centre checks", "Complete manual CC checklist.", "10 min", "Operator"),
    "cp3_approve": ("Lab sign-off (cp3)", "Approve lab validation results.", "5 min", "Lead"),
    "ship_prep": ("Ship preparation", "Review production deployment map.", "10 min", "Operator"),
    "cp4_approve": ("Handover (cp4)", "Final handover approval.", "5 min", "Client"),
    "export": ("Export pipeline", "Generate CSV export for CRM.", "2 min", "Sales"),
}


def goal_banner(step_id: str) -> FT:
    title, goal, est, approver = STEP_GOALS.get(step_id, (step_id, "", "", ""))
    return Card(
        Div(cls="flex justify-between items-start")(
            Div(H3(title, cls="font-semibold"), P(goal, cls="text-slate-600 text-sm mt-1")),
            Div(cls="text-right text-sm text-slate-500")(
                P(f"Est. {est}"),
                P(f"Approver: {approver}"),
            ),
        ),
        cls="mb-4",
    )
