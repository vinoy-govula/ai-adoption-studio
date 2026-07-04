from __future__ import annotations

from pathlib import Path

import pytest

from ai_adoption_studio.adapters.delivery_validator import DeploymentOrchestrator


def test_validator_cwd_rejects_invalid_directory(tmp_path: Path) -> None:
    orchestrator = DeploymentOrchestrator(tmp_path / "missing-validator")

    with pytest.raises(RuntimeError, match="STUDIO_DELIVERY_VALIDATOR_ROOT"):
        orchestrator._validator_cwd()


def test_validator_cwd_resolves_valid_directory(tmp_path: Path) -> None:
    validator_root = tmp_path / "ai-delivery-validator"
    validator_root.mkdir()
    orchestrator = DeploymentOrchestrator(validator_root)

    assert orchestrator._validator_cwd() == str(validator_root.resolve())


@pytest.mark.asyncio
async def test_generate_kit_passes_absolute_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    validator_root = tmp_path / "ai-delivery-validator"
    validator_root.mkdir()
    lead_dir = Path("data") / "lead-1"
    lead_dir.mkdir(parents=True)
    assessment_path = lead_dir / "assessment-report.json"
    assessment_path.write_text("{}", encoding="utf-8")
    captured: dict[str, object] = {}

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, None]:
            (lead_dir / "playground-kit.manifest.json").write_text("{}", encoding="utf-8")
            return b"ok", None

    async def fake_create_subprocess_exec(*args: str, **kwargs: object) -> FakeProcess:
        captured["args"] = args
        captured["cwd"] = kwargs["cwd"]
        return FakeProcess()

    monkeypatch.setattr(
        "ai_adoption_studio.adapters.delivery_validator.asyncio.create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    orchestrator = DeploymentOrchestrator(validator_root)

    manifest_path = await orchestrator.generate_kit(
        "lead-1",
        assessment_path,
        {"client_slug": "test"},
        lead_dir,
    )

    args = captured["args"]
    assert isinstance(args, tuple)
    assert str(assessment_path.resolve()) in args
    assert str((lead_dir / "branding.json").resolve()) in args
    assert str(lead_dir.resolve()) in args
    assert captured["cwd"] == str(validator_root.resolve())
    assert manifest_path == lead_dir.resolve() / "playground-kit.manifest.json"
