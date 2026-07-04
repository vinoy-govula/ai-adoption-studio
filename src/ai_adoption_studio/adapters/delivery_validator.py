"""Subprocess adapter for ai-delivery-validator."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from ai_adoption_studio.config import settings


class DeploymentOrchestrator:
    """Invoke delivery-validator CLIs via subprocess."""

    def __init__(self, validator_root: Path | None = None) -> None:
        self._root = validator_root or settings.delivery_validator_root

    def _validator_cwd(self) -> str:
        root = self._root.resolve()
        if not root.is_dir():
            raise RuntimeError(
                "Delivery validator root is not a valid directory: "
                f"{root}. Set STUDIO_DELIVERY_VALIDATOR_ROOT with forward slashes, "
                'for example "../ai-delivery-validator".'
            )
        return str(root)

    def _path_arg(self, path: Path) -> str:
        return str(path.resolve())

    def _uv_cmd(self, script: str, *args: str) -> list[str]:
        if sys.platform == "win32":
            return ["uv", "run", script, *args]
        return ["uv", "run", script, *args]

    def _env(self, capability: str | None = None, manifest_path: Path | None = None) -> dict[str, str]:
        import json
        import os

        from ai_adoption_studio.services.infrastructure_urls import resolve_urls

        env = os.environ.copy()
        env["RUNTIME_MANAGER_BASE_URL"] = settings.runtime_manager_base_url
        gateway_base = settings.gateway_base_url
        if manifest_path and manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            gateway_base = resolve_urls(manifest).gateway_base_url
        env["AI_PLATFORM_BASE_URL"] = gateway_base
        env["DEPLOYMENT_CATALOG_ROOT"] = str(settings.deployment_catalog_root.resolve())
        if settings.platform_api_key:
            env["AI_PLATFORM_API_KEY"] = settings.platform_api_key
        if capability:
            env["STUDIO_VALIDATION_CAPABILITY"] = capability
        return env

    async def generate_kit(
        self,
        lead_id: str,
        assessment_path: Path,
        branding: dict[str, Any],
        output_dir: Path,
        *,
        log_path: Path | None = None,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        branding_path = output_dir / "branding.json"
        branding_path.write_text(json.dumps(branding, indent=2), encoding="utf-8")
        assessment_path = assessment_path.resolve()
        branding_path = branding_path.resolve()
        output_dir = output_dir.resolve()

        cmd = self._uv_cmd(
            "delivery-generate-kit",
            "--assessment",
            self._path_arg(assessment_path),
            "--branding",
            self._path_arg(branding_path),
            "--output-dir",
            self._path_arg(output_dir),
            "--runtime-manager-url",
            settings.runtime_manager_base_url,
        )
        if branding.get("public_url"):
            cmd.extend(["--public-url", str(branding["public_url"])])
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self._validator_cwd(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=self._env(),
        )
        stdout, _ = await proc.communicate()
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_bytes(stdout or b"")
        if proc.returncode != 0:
            raise RuntimeError(f"Kit generation failed (exit {proc.returncode})")
        manifest = output_dir / "playground-kit.manifest.json"
        if not manifest.exists():
            raise FileNotFoundError("Manifest not produced")
        return manifest

    async def deploy_lab(
        self,
        manifest_path: Path,
        staging_dir: Path,
        *,
        job_id: str,
        log_path: Path,
    ) -> int:
        staging_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_path.resolve()
        staging_dir = staging_dir.resolve()
        cmd = self._uv_cmd(
            "delivery-deploy-lab",
            "--manifest",
            self._path_arg(manifest_path),
            "--staging-dir",
            self._path_arg(staging_dir),
            "--deployment-catalog-root",
            self._path_arg(settings.deployment_catalog_root),
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("ab") as log_file:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self._validator_cwd(),
                stdout=log_file,
                stderr=asyncio.subprocess.STDOUT,
                env=self._env(manifest_path=manifest_path),
            )
            return await proc.wait()

    async def validate(
        self,
        manifest_path: Path,
        output_dir: Path,
        *,
        job_id: str,
        capability: str,
        log_path: Path,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_path.resolve()
        output_dir = output_dir.resolve()
        cmd = self._uv_cmd(
            "delivery-validate",
            "--manifest",
            self._path_arg(manifest_path),
            "--output-dir",
            self._path_arg(output_dir),
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("ab") as log_file:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self._validator_cwd(),
                stdout=log_file,
                stderr=asyncio.subprocess.STDOUT,
                env=self._env(capability, manifest_path=manifest_path),
            )
            exit_code = await proc.wait()
        report_path = output_dir / "deployment-report.json"
        if exit_code != 0 and not report_path.exists():
            raise RuntimeError(f"Validation failed (exit {exit_code})")
        return report_path
