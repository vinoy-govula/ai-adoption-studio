from __future__ import annotations

from pathlib import Path

import pytest

from ai_adoption_studio.ops import orchestrator as orch
from ai_adoption_studio.ops.orchestrator import Paths, Prerequisite


def _make_paths(tmp_path: Path, *, with_repos: bool = True, with_template: bool = True) -> Paths:
    workspace = tmp_path
    studio_root = workspace / "ai-adoption-studio"
    studio_root.mkdir(parents=True, exist_ok=True)
    paths = Paths(
        workspace_root=workspace,
        studio_root=studio_root,
        deployment_catalog=workspace / "deployment-catalog",
        env_file=studio_root / ".env",
        env_example=studio_root / ".env.example",
    )
    if with_template:
        paths.env_example.write_text("STUDIO_PORT=8010\n", encoding="utf-8")
    if with_repos:
        for repo in paths.sibling_repos:
            (workspace / repo).mkdir(parents=True, exist_ok=True)
    return paths


def test_ensure_config_creates_when_missing(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    created = orch.ensure_config(paths)
    assert created is True
    assert paths.env_file.exists()
    assert "STUDIO_PORT=8010" in paths.env_file.read_text(encoding="utf-8")


def test_ensure_config_is_noop_when_present(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    paths.env_file.write_text("STUDIO_PORT=9999\n", encoding="utf-8")
    created = orch.ensure_config(paths)
    assert created is False
    assert "9999" in paths.env_file.read_text(encoding="utf-8")


def test_check_prerequisites_flags_missing_tools_and_repos(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path, with_repos=False)
    results = orch.check_prerequisites(paths, which=lambda _tool: None)
    by_name = {p.name: p for p in results}
    assert by_name["docker"].ok is False
    assert by_name["uv"].ok is False
    assert by_name["repo:ai-gateway"].ok is False


def test_check_prerequisites_passes_when_satisfied(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    results = orch.check_prerequisites(paths, which=lambda tool: f"/usr/bin/{tool}")
    assert all(p.ok for p in results), [p for p in results if not p.ok]


def test_up_happy_path_orders_steps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _make_paths(tmp_path)
    monkeypatch.setattr(
        orch,
        "check_prerequisites",
        lambda p, **_: [Prerequisite("all", True, "ok")],
    )
    calls: list[str] = []

    def runner(cmd: list[str], cwd: Path) -> None:
        calls.append("compose:" + " ".join(cmd))

    def spawn(cmd: list[str], cwd: Path) -> None:
        calls.append("spawn:" + " ".join(cmd))

    result = orch.up(paths, runner=runner, spawn=spawn, health_wait=lambda _url: True)

    assert result.ok is True
    assert result.config_created is True
    assert result.compose_started is True
    assert result.studio_launched is True
    assert all(result.health.values())
    assert any(c.startswith("compose:docker compose up -d") for c in calls)
    assert any("uvicorn" in c for c in calls)
    # compose must run before studio launch
    assert next(i for i, c in enumerate(calls) if c.startswith("compose:")) < next(
        i for i, c in enumerate(calls) if c.startswith("spawn:")
    )


def test_up_stops_when_health_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _make_paths(tmp_path)
    monkeypatch.setattr(
        orch, "check_prerequisites", lambda p, **_: [Prerequisite("all", True, "ok")]
    )
    spawned: list[str] = []

    result = orch.up(
        paths,
        runner=lambda cmd, cwd: None,
        spawn=lambda cmd, cwd: spawned.append("x"),
        health_wait=lambda _url: False,
    )

    assert result.ok is False
    assert result.studio_launched is False
    assert spawned == []
    assert result.problems


def test_up_aborts_on_missing_prerequisites(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _make_paths(tmp_path)
    monkeypatch.setattr(
        orch,
        "check_prerequisites",
        lambda p, **_: [Prerequisite("docker", False, "docker not found on PATH")],
    )
    ran: list[str] = []

    result = orch.up(
        paths,
        runner=lambda cmd, cwd: ran.append("compose"),
        spawn=lambda cmd, cwd: ran.append("spawn"),
        health_wait=lambda _url: True,
    )

    assert result.ok is False
    assert result.compose_started is False
    assert ran == []
    assert any("docker" in problem for problem in result.problems)


def test_wait_for_health_returns_true_once_healthy() -> None:
    attempts = {"n": 0}

    def fake_probe(url: str, *, client=None) -> bool:
        attempts["n"] += 1
        return attempts["n"] >= 2

    import ai_adoption_studio.ops.orchestrator as module

    original = module.probe_health
    module.probe_health = fake_probe  # type: ignore[assignment]
    try:
        ok = orch.wait_for_health(
            "http://x/healthz", timeout=10, interval=0, sleep=lambda _s: None
        )
    finally:
        module.probe_health = original  # type: ignore[assignment]
    assert ok is True
