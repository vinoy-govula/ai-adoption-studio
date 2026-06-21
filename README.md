# AI Adoption Studio

Internal operator tool for EOI intake, AI readiness assessment, checkpoint workflow, and pipeline CSV export.

## Prerequisites

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13. Sibling checkout of [ai-runtime-manager](../ai-runtime-manager) is required (path dependency).

Start the platform stack first — see [deployment-catalog/README.md](../deployment-catalog/README.md) (Gateway local bootstrap + ARM/Control Centre in Docker). For LLM narratives, point `LOCAL_LLM_BASE_URL` at your existing inference (e.g. vllm_server on `http://localhost/v1`).

## Quick start

```powershell
cd ai-adoption-studio
uv venv --python 3.13
uv sync --extra dev

$env:STUDIO_DATA_ROOT = ".\data"
$env:STUDIO_INTERNAL_API_KEY = "dev-key"
$env:LOCAL_LLM_BASE_URL = "http://localhost/v1"

uv run uvicorn ai_adoption_studio.main:app --reload --port 8010
```

## Run Tests

```powershell
uv run pytest -v
```

- Internal UI: http://localhost:8010/
- Public EOI API: `POST http://localhost:8010/api/v1/eoi`

## Environment

| Variable | Purpose |
|----------|---------|
| `STUDIO_DATA_ROOT` | Artifact storage root (default `./data`) |
| `STUDIO_INTERNAL_API_KEY` | Internal API/UI auth key |
| `LOCAL_LLM_BASE_URL` | Internal narrative generation |
