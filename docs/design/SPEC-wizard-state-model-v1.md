# SPEC — Wizard State Model v1

**Status:** Draft for review  
**Parent spec:** [ARCH-adoption-studio-wizard-v1.md](./ARCH-adoption-studio-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. workflow-state.json schema

Stored at `{STUDIO_DATA_ROOT}/{lead_id}/workflow-state.json`.

```json
{
  "schema_version": "1.0.0",
  "lead_id": "lead-20260621-abc123",
  "current_step": "assessment_form",
  "updated_at": "2026-06-21T10:00:00Z",
  "updated_by": "operator@example.com",
  "steps": {
    "eoi_review": { "status": "complete", "completed_at": "..." },
    "qualify": { "status": "complete", "completed_at": "..." },
    "assessment_form": { "status": "in_progress", "completed_at": null }
  },
  "validation": {
    "test_capability": "chat",
    "test_model_override": null,
    "test_prompt": "Summarize this deployment in one sentence.",
    "last_smoke_result": {
      "status": "passed",
      "latency_ms": 842,
      "at": "2026-06-21T10:05:00Z"
    }
  },
  "artifact_versions": {
    "assessment-report": 2,
    "playground-kit.manifest": 1
  },
  "active_jobs": {
    "deploy": "job-uuid",
    "validate": null
  }
}
```

---

## 2. Step status enum

| Status | Meaning |
|--------|---------|
| `locked` | Prerequisites not met |
| `available` | Can enter |
| `in_progress` | Operator viewing/editing |
| `complete` | Step finished |
| `blocked` | Error or invalidation |

---

## 3. Step unlock rules

| Step | Unlocks when |
|------|--------------|
| `eoi_review` | `eoi-intent.json` exists |
| `qualify` | eoi_review complete |
| `assessment_form` | cp1 recorded OR pipeline_status qualified |
| `assessment_run` | internal-responses.json valid |
| `narrative` | assessment-report.json exists |
| `cp2_approve` | assessment-report exists |
| `branding_kit` | cp2 approved |
| `deploy_lab` | manifest exists + cp2 |
| `live_status` | manifest status active/deploying |
| `llm_test_select` | Gateway reachable (or skip with warning) |
| `validate` | capability selected + deploy active |
| `manual_cc` | deployment-report exists (any status) |
| `cp3_approve` | validation passed + checklist complete |
| `ship_prep` | cp3 approved |
| `cp4_approve` | ship_prep viewed |
| `export` | cp4 approved |

---

## 4. Artifact versioning

When upstream artifact changes:

- Increment `artifact_versions` key
- If change after cp2: set manifest `status=draft`, block deploy/validate until cp2 re-confirmed (banner)

---

## 5. Job records

`{lead_id}/jobs/{job_id}.json`:

```json
{
  "job_id": "uuid",
  "type": "deploy|validate|cursor_certify|smoke_test",
  "status": "queued|running|succeeded|failed|cancelled",
  "created_at": "...",
  "started_at": null,
  "completed_at": null,
  "progress_pct": 0,
  "message": "",
  "log_path": "jobs/{job_id}.log",
  "exit_code": null,
  "metadata": {}
}
```

---

## 6. Concurrency

- One active deploy job per lead
- One active validate job per lead
- Wizard service uses file lock (`portalocker` or `fcntl`) on workflow-state.json writes

---

## 7. Resume after failure

- Failed deploy: step stays `deploy_lab`, job `failed`, operator can retry (new job_id)
- Failed validation: step `validate`, report preserved, re-run creates new report version

---

## 8. WizardService API (proposed)

```python
class WizardService:
    def get_state(lead_id: str) -> WorkflowState: ...
    def advance(lead_id: str, step_id: str, *, actor: str) -> WorkflowState: ...
    def go_back(lead_id: str, step_id: str) -> WorkflowState: ...
    def save_draft(lead_id: str, step_id: str, payload: dict) -> WorkflowState: ...
    def invalidate_downstream(lead_id: str, from_step: str) -> None: ...
```

---

## 9. Implementation checklist

- [ ] `models/workflow_state.py` — Pydantic models
- [ ] `services/wizard_service.py`
- [ ] Migrate existing leads: default workflow-state on first open

---

**See also:** [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md)
