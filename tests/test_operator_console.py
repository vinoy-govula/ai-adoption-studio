from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from ai_adoption_studio.config import settings
from ai_adoption_studio.main import app
from ai_adoption_studio.models.job_record import JobStatus
from ai_adoption_studio.routes.api_jobs import sse_log_events
from ai_adoption_studio.services.command_palette import (
    COMMAND_ALLOW_LIST,
    CommandPalette,
    UnknownCommandError,
    get_command,
    is_allowed,
)
from ai_adoption_studio.services.job_runner import JobRunner
from ai_adoption_studio.services.store import LeadStore


class _FakeJobs:
    def __init__(self) -> None:
        self.spawned: list[tuple[str, str]] = []

    def spawn(self, lead_id: str, job_type: str, handler):  # noqa: ANN001
        self.spawned.append((lead_id, job_type))
        return type("J", (), {"job_id": "job-x", "type": job_type})()


def test_allow_list_membership() -> None:
    assert is_allowed("deploy_lab") is True
    assert is_allowed("rm -rf /") is False
    assert set(COMMAND_ALLOW_LIST) == {"health", "deploy_lab", "validate", "tail"}


def test_get_command_rejects_unknown() -> None:
    with pytest.raises(UnknownCommandError):
        get_command("shutdown")


def test_palette_runs_allow_listed_action() -> None:
    fake = _FakeJobs()
    palette = CommandPalette(fake, {"validate": lambda job: 0})
    palette.run("lead-1", "validate")
    assert fake.spawned == [("lead-1", "validate")]


def test_palette_refuses_unknown_action() -> None:
    fake = _FakeJobs()
    palette = CommandPalette(fake, {"validate": lambda job: 0})
    with pytest.raises(UnknownCommandError):
        palette.run("lead-1", "definitely_not_allowed")
    assert fake.spawned == []


def test_palette_refuses_action_without_handler() -> None:
    fake = _FakeJobs()
    palette = CommandPalette(fake, {})  # allow-listed but no handler wired
    with pytest.raises(UnknownCommandError):
        palette.run("lead-1", "deploy_lab")
    assert fake.spawned == []


@pytest.mark.asyncio
async def test_sse_log_events_streams_then_done(tmp_path: Path) -> None:
    store = LeadStore(tmp_path)
    jobs = JobRunner(store)
    record = store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "X"}}
    )
    lead_id = record["lead_id"]
    job = jobs.create_job(lead_id, "deploy_lab")
    log_path = jobs._log_path(lead_id, job.job_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("line one\nline two\n", encoding="utf-8")
    job.status = JobStatus.SUCCEEDED
    jobs.update_job(lead_id, job)

    frames = [frame async for frame in sse_log_events(jobs, lead_id, job.job_id)]

    assert "data: line one\n\n" in frames
    assert "data: line two\n\n" in frames
    assert frames[-1] == "event: done\ndata: succeeded\n\n"


@pytest.mark.asyncio
async def test_sse_endpoint_requires_auth_and_streams(tmp_path: Path, monkeypatch) -> None:
    # The registered route closes over main.lead_store / main._jobs (which share
    # one ArtifactStore). Repoint that shared root at a temp dir for isolation.
    from ai_adoption_studio.main import _jobs as jobs
    from ai_adoption_studio.main import lead_store as store

    monkeypatch.setattr(store._store, "root", tmp_path)

    record = store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "X"}}
    )
    lead_id = record["lead_id"]
    job = jobs.create_job(lead_id, "deploy_lab")
    log_path = jobs._log_path(lead_id, job.job_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("hello\n", encoding="utf-8")
    job.status = JobStatus.SUCCEEDED
    jobs.update_job(lead_id, job)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauth = await client.get(f"/api/jobs/{job.job_id}/stream?lead_id={lead_id}")
        assert unauth.status_code == 401

        resp = await client.get(
            f"/api/jobs/{job.job_id}/stream?lead_id={lead_id}&k={settings.internal_api_key}"
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert "data: hello" in resp.text
        assert "event: done" in resp.text


@pytest.mark.asyncio
async def test_job_log_download_returns_log_file(tmp_path: Path, monkeypatch) -> None:
    from ai_adoption_studio.main import _jobs as jobs
    from ai_adoption_studio.main import lead_store as store

    monkeypatch.setattr(store._store, "root", tmp_path)

    record = store.create_eoi(
        {"consent": {"privacy_policy_accepted": True, "contact_permitted": True}, "responses": {"org_name": "X"}}
    )
    lead_id = record["lead_id"]
    job = jobs.create_job(lead_id, "deploy")
    log_path = jobs._log_path(lead_id, job.job_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("deploy line\nERROR failed\n", encoding="utf-8")
    jobs.update_job(lead_id, job)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {settings.internal_api_key}"},
    ) as client:
        response = await client.get(f"/api/jobs/{job.job_id}/log/download?lead_id={lead_id}")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "deploy line" in response.text
    assert "ERROR failed" in response.text
    assert f"{lead_id}-{job.job_id}.log" in response.headers["content-disposition"]
