"""Wizard service unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_adoption_studio.models.workflow_state import StepStatus
from ai_adoption_studio.services.store import LeadStore
from ai_adoption_studio.services.wizard_service import WizardService


@pytest.fixture
def wizard(tmp_path: Path) -> WizardService:
    store = LeadStore(tmp_path)
    return WizardService(store)


def test_eoi_review_unlocks_when_eoi_exists(wizard: WizardService, tmp_path: Path) -> None:
    store = wizard._store
    record = store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "Acme"}}
    )
    state = wizard.ensure_state(record["lead_id"])
    assert state.steps["eoi_review"].status in {StepStatus.AVAILABLE, StepStatus.IN_PROGRESS}


def test_qualify_unlocks_after_eoi_review_complete(wizard: WizardService) -> None:
    record = wizard._store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "Acme"}}
    )
    lead_id = record["lead_id"]
    wizard.advance(lead_id, "eoi_review")
    state = wizard.get_state(lead_id)
    assert state.steps["qualify"].status in {StepStatus.AVAILABLE, StepStatus.IN_PROGRESS, StepStatus.COMPLETE}


def test_go_back_moves_to_previous_step(wizard: WizardService) -> None:
    record = wizard._store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "Acme"}}
    )
    lead_id = record["lead_id"]
    wizard.advance(lead_id, "eoi_review")
    wizard.advance(lead_id, "qualify", actor="sales@example.com")
    state = wizard.go_back(lead_id)
    assert state.current_step == "qualify"


def test_invalidate_downstream_resets_steps(wizard: WizardService) -> None:
    record = wizard._store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "Acme"}}
    )
    lead_id = record["lead_id"]
    wizard.advance(lead_id, "eoi_review")
    wizard.advance(lead_id, "qualify")
    wizard.invalidate_downstream(lead_id, "eoi_review")
    state = wizard.get_state(lead_id)
    assert state.steps["qualify"].status == StepStatus.LOCKED
