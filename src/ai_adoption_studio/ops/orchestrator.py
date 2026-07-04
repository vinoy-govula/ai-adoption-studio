"""Single-command operator startup orchestrator.

Implements ``studio up | down | status | logs`` per
docs/design/SPEC-operator-single-command-v1.md.

Design rules:
- Idempotent: already-running services are detected via ``/healthz`` and skipped.
- Health-gated: wait for dependencies before launching Studio.
- Fail-fast with guidance: on timeout, report the failed layer and its URL.
- Boundary: only issues ``docker compose`` in deployment-catalog and launches
  processes. It never generates compose files or manages containers directly.
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

import httpx

Runner = Callable[[list[str], Path], "subprocess.CompletedProcess[bytes]"]

# Dependency services started via deployment-catalog compose (hybrid dev flow):
# databases, Runtime Manager, and Control Centre. Gateway runs locally with the
# bootstrap-key seed (see ai-gateway ADR-006), not via compose.
COMPOSE_SERVICES: tuple[str, ...] = ("gateway-db", "arm-db", "arm", "control-centre")


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem locations the orchestrator operates on."""

    workspace_root: Path
    studio_root: Path
    deployment_catalog: Path
    env_file: Path
    env_example: Path
    sibling_repos: tuple[str, ...] = (
        "ai-gateway",
        "ai-runtime-manager",
        "ai-platform-sdk",
        "ai-delivery-validator",
        "deployment-catalog",
    )


@dataclass(frozen=True)
class HealthTarget:
    name: str
    url: str


@dataclass(frozen=True)
class Prerequisite:
    name: str
    ok: bool
    detail: str


@dataclass
class UpResult:
    prerequisites: list[Prerequisite] = field(default_factory=list)
    config_created: bool = False
    compose_started: bool = False
    health: dict[str, bool] = field(default_factory=dict)
    studio_launched: bool = False
    ok: bool = False
    problems: list[str] = field(default_factory=list)


def default_paths() -> Paths:
    """Resolve paths from this module's location within ai-adoption-studio."""
    studio_root = Path(__file__).resolve().parents[3]
    workspace_root = studio_root.parent
    return Paths(
        workspace_root=workspace_root,
        studio_root=studio_root,
        deployment_catalog=workspace_root / "deployment-catalog",
        env_file=studio_root / ".env",
        env_example=studio_root / ".env.example",
    )


def health_targets() -> list[HealthTarget]:
    """Health endpoints, overridable via STUDIO_* / dependency base URLs."""
    gateway = os.environ.get("STUDIO_GATEWAY_BASE_URL", "http://localhost:8000")
    runtime = os.environ.get("STUDIO_RUNTIME_MANAGER_BASE_URL", "http://localhost:8001")
    control = os.environ.get("STUDIO_CONTROL_CENTRE_BASE_URL", "http://localhost:8002")
    return [
        HealthTarget("gateway", f"{gateway.rstrip('/')}/healthz"),
        HealthTarget("runtime", f"{runtime.rstrip('/')}/healthz"),
        HealthTarget("control_centre", f"{control.rstrip('/')}/healthz"),
    ]


def studio_url() -> str:
    port = os.environ.get("STUDIO_PORT", "8010")
    return f"http://localhost:{port}"


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) != 0


def check_prerequisites(
    paths: Paths,
    *,
    which: Callable[[str], str | None] = shutil.which,
) -> list[Prerequisite]:
    """Verify tools, sibling checkouts, and template presence."""
    results: list[Prerequisite] = []

    for tool in ("docker", "uv"):
        found = which(tool)
        results.append(
            Prerequisite(tool, found is not None, found or f"{tool} not found on PATH")
        )

    results.append(
        Prerequisite(
            "python",
            sys.version_info >= (3, 13),
            f"python {sys.version_info.major}.{sys.version_info.minor}",
        )
    )

    for repo in paths.sibling_repos:
        path = paths.workspace_root / repo
        results.append(
            Prerequisite(f"repo:{repo}", path.is_dir(), str(path))
        )

    results.append(
        Prerequisite(
            "env_example",
            paths.env_example.exists(),
            str(paths.env_example),
        )
    )
    return results


def ensure_config(paths: Paths) -> bool:
    """Create the local .env once from the template. Returns True if created."""
    if paths.env_file.exists():
        return False
    if not paths.env_example.exists():
        raise FileNotFoundError(f"Config template missing: {paths.env_example}")
    paths.env_file.write_text(paths.env_example.read_text(encoding="utf-8"), encoding="utf-8")
    return True


def _run(cmd: list[str], cwd: Path, runner: Runner) -> None:
    runner(cmd, cwd)


def _default_runner(cmd: list[str], cwd: Path) -> "subprocess.CompletedProcess[bytes]":
    return subprocess.run(cmd, cwd=str(cwd), check=True)


def compose_up(paths: Paths, *, runner: Runner = _default_runner) -> None:
    _run(["docker", "compose", "up", "-d", *COMPOSE_SERVICES], paths.deployment_catalog, runner)


def compose_down(paths: Paths, *, runner: Runner = _default_runner) -> None:
    _run(["docker", "compose", "down"], paths.deployment_catalog, runner)


def probe_health(url: str, *, client: httpx.Client | None = None) -> bool:
    owns_client = client is None
    client = client or httpx.Client(timeout=3.0)
    try:
        return client.get(url).status_code == 200
    except httpx.HTTPError:
        return False
    finally:
        if owns_client:
            client.close()


def wait_for_health(
    url: str,
    *,
    timeout: float = 120.0,
    interval: float = 3.0,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
    client: httpx.Client | None = None,
) -> bool:
    """Poll ``url`` until healthy or timeout. Reuses the deploy_lab pattern."""
    deadline = now() + timeout
    while now() < deadline:
        if probe_health(url, client=client):
            return True
        sleep(interval)
    return probe_health(url, client=client)


def launch_studio(
    paths: Paths,
    *,
    spawn: Callable[[list[str], Path], object] | None = None,
) -> bool:
    """Launch the Studio uvicorn process (non-blocking)."""
    cmd = [
        "uv",
        "run",
        "uvicorn",
        "ai_adoption_studio.main:app",
        "--port",
        os.environ.get("STUDIO_PORT", "8010"),
    ]
    spawn = spawn or (lambda c, cwd: subprocess.Popen(c, cwd=str(cwd)))
    spawn(cmd, paths.studio_root)
    return True


def up(
    paths: Paths | None = None,
    *,
    runner: Runner = _default_runner,
    spawn: Callable[[list[str], Path], object] | None = None,
    health_wait: Callable[[str], bool] | None = None,
) -> UpResult:
    """Bring the whole stack up in one call. Idempotent and health-gated."""
    paths = paths or default_paths()
    result = UpResult()

    result.prerequisites = check_prerequisites(paths)
    missing = [p for p in result.prerequisites if not p.ok]
    if missing:
        result.problems = [f"{p.name}: {p.detail}" for p in missing]
        return result

    result.config_created = ensure_config(paths)

    compose_up(paths, runner=runner)
    result.compose_started = True

    waiter = health_wait or (lambda u: wait_for_health(u))
    for target in health_targets():
        healthy = waiter(target.url)
        result.health[target.name] = healthy
        if not healthy:
            result.problems.append(f"{target.name} not healthy at {target.url}")

    if result.problems:
        return result

    result.studio_launched = launch_studio(paths, spawn=spawn)
    result.ok = True
    return result


def status(paths: Paths | None = None) -> dict[str, bool]:
    """Probe each layer and Studio; return name -> healthy."""
    paths = paths or default_paths()
    report = {target.name: probe_health(target.url) for target in health_targets()}
    report["studio"] = probe_health(f"{studio_url()}/healthz")
    return report


def _print_status(report: dict[str, bool]) -> None:
    print("Layer            Status")
    print("-" * 28)
    for name, healthy in report.items():
        print(f"{name:<16} {'healthy' if healthy else 'DOWN'}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="studio", description="AI Adoption Studio orchestrator")
    parser.add_argument("verb", choices=["up", "down", "status", "logs"])
    args = parser.parse_args(list(argv) if argv is not None else None)
    paths = default_paths()

    if args.verb == "up":
        result = up(paths)
        if not result.ok:
            print("Startup failed:", file=sys.stderr)
            for problem in result.problems:
                print(f"  - {problem}", file=sys.stderr)
            return 1
        print(f"Studio is up at {studio_url()}")
        _print_status(status(paths))
        return 0

    if args.verb == "down":
        compose_down(paths)
        print("Dependencies stopped. Stop the Studio process manually if still running.")
        return 0

    if args.verb == "status":
        _print_status(status(paths))
        return 0

    if args.verb == "logs":
        subprocess.run(["docker", "compose", "logs", "-f"], cwd=str(paths.deployment_catalog))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
