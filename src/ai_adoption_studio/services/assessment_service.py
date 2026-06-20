"""Assessment workflow orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_runtime_manager.assessment.checkpoints import approve_checkpoint
from ai_runtime_manager.assessment.report_builder import build_assessment_report
from ai_runtime_manager.assessment.narrative import write_narrative_file
from ai_runtime_manager.export.pipeline_csv import export_pipeline_csv

from ai_adoption_studio.services.store import LeadStore


async def run_assessment(
    store: LeadStore,
    lead_id: str,
    internal: dict[str, Any],
    *,
    lab_has_gpu: bool = True,
) -> dict[str, Any]:
    eoi = store.get_eoi(lead_id)
    store.save_internal_responses(lead_id, internal)
    cp1 = eoi.get("pipeline_status") in {"qualified", "converted"}
    report = build_assessment_report(
        eoi,
        internal,
        status="approved_for_pursuit" if cp1 else "draft",
        cp0_approved=True,
        cp1_approved=cp1,
        lab_has_gpu=lab_has_gpu,
    )
    store.save_assessment_report(lead_id, report)
    await write_narrative_file(report, store._store.lead_dir(lead_id), use_llm=False)
    return report


async def regenerate_narrative(
    store: LeadStore,
    lead_id: str,
    *,
    use_llm: bool = True,
) -> Path:
    report = store.get_assessment_report(lead_id)
    if report is None:
        raise ValueError("Assessment report not found")
    return await write_narrative_file(
        report,
        store._store.lead_dir(lead_id),
        use_llm=use_llm,
    )


def qualify_lead(store: LeadStore, lead_id: str, actor: str) -> dict[str, Any]:
    eoi = store.get_eoi(lead_id)
    eoi["pipeline_status"] = "qualified"
    store._store.write_json(lead_id, "eoi-intent.json", eoi)
    report = store.get_assessment_report(lead_id)
    if report:
        report = approve_checkpoint(report, "cp1_lead_qualified", actor=actor)
        store.save_assessment_report(lead_id, report)
    return eoi


def approve_assessment_checkpoint(
    store: LeadStore,
    lead_id: str,
    *,
    actor: str,
    notes: str = "",
) -> dict[str, Any]:
    report = store.get_assessment_report(lead_id)
    if report is None:
        raise ValueError("Assessment report not found")
    updated = approve_checkpoint(
        report,
        "cp2_assessment_approved",
        actor=actor,
        notes=notes,
    )
    updated["status"] = "approved_for_deployment"
    store.save_assessment_report(lead_id, updated)
    return updated


def export_csv(store: LeadStore, output_dir: Path, *, as_zip: bool = True) -> list[Path]:
    return export_pipeline_csv(store.artifact_root, output_dir, as_zip=as_zip)
