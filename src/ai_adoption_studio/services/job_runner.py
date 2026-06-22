"""Background job execution and persistence."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Coroutine

from ai_adoption_studio.models.job_record import JobRecord, JobStatus
from ai_adoption_studio.services.store import LeadStore
from ai_adoption_studio.services.wizard_service import WizardService


class JobRunner:
    """Create and track async background jobs per lead."""

    def __init__(self, store: LeadStore | None = None, wizard: WizardService | None = None) -> None:
        self._store = store or LeadStore()
        self._wizard = wizard or WizardService(self._store)

    def _jobs_dir(self, lead_id: str) -> Path:
        return self._store._store.lead_dir(lead_id) / "jobs"

    def _job_path(self, lead_id: str, job_id: str) -> Path:
        return self._jobs_dir(lead_id) / f"{job_id}.json"

    def _log_path(self, lead_id: str, job_id: str) -> Path:
        return self._jobs_dir(lead_id) / f"{job_id}.log"

    def create_job(self, lead_id: str, job_type: str, metadata: dict[str, Any] | None = None) -> JobRecord:
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        log_rel = f"jobs/{job_id}.log"
        record = JobRecord(
            job_id=job_id,
            lead_id=lead_id,
            type=job_type,
            log_path=log_rel,
            metadata=metadata or {},
        )
        self._jobs_dir(lead_id).mkdir(parents=True, exist_ok=True)
        self._job_path(lead_id, job_id).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def get_job(self, lead_id: str, job_id: str) -> JobRecord:
        path = self._job_path(lead_id, job_id)
        if not path.exists():
            raise FileNotFoundError(job_id)
        return JobRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def update_job(self, lead_id: str, job: JobRecord) -> JobRecord:
        self._job_path(lead_id, job.job_id).write_text(job.model_dump_json(indent=2), encoding="utf-8")
        return job

    def tail_log(self, lead_id: str, job_id: str, *, tail: int = 50) -> str:
        path = self._log_path(lead_id, job_id)
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-tail:])

    def spawn(
        self,
        lead_id: str,
        job_type: str,
        coro_factory: Callable[[JobRecord], Coroutine[Any, Any, int]],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> JobRecord:
        job = self.create_job(lead_id, job_type, metadata)
        self._wizard.set_active_job(lead_id, job_type, job.job_id)

        async def _run() -> None:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(UTC).isoformat()
            self.update_job(lead_id, job)
            try:
                exit_code = await coro_factory(job)
                job.exit_code = exit_code
                job.status = JobStatus.SUCCEEDED if exit_code == 0 else JobStatus.FAILED
                job.progress_pct = 100
                job.message = "Completed" if exit_code == 0 else f"Failed with exit {exit_code}"
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.message = str(exc)
                job.exit_code = 1
                log_path = self._log_path(lead_id, job.job_id)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with log_path.open("a", encoding="utf-8") as fh:
                    fh.write(f"\nERROR: {exc}\n")
            finally:
                job.completed_at = datetime.now(UTC).isoformat()
                self.update_job(lead_id, job)
                self._wizard.set_active_job(lead_id, job_type, None)

        asyncio.create_task(_run())
        return job


job_runner = JobRunner()
