# AI Adoption Studio

Internal operator **web wizard** for EOI intake, AI readiness assessment, playground deploy, validation, and pipeline CSV export.

Operator docs and question sets: [docs/README.md](docs/README.md). **Wizard design pack:** [docs/design/README.md](docs/design/README.md) (FastHTML + MonsterUI + HTMX). JSON schemas and engine specs: [ai-runtime-manager/docs/adoption-studio](../ai-runtime-manager/docs/adoption-studio/README.md).

## Prerequisites

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13. Sibling checkouts of [ai-runtime-manager](../ai-runtime-manager) and [ai-platform-sdk](../ai-platform-sdk) are required (path dependencies).

Start the platform stack first — see [deployment-catalog/README.md](../deployment-catalog/README.md).

## Quick start

```powershell
cd ai-adoption-studio
uv venv --python 3.13
uv sync --extra dev

$env:STUDIO_DATA_ROOT = ".\data"
$env:STUDIO_INTERNAL_API_KEY = "dev-key"
$env:STUDIO_PLATFORM_API_KEY = "your-gateway-key"
$env:STUDIO_GATEWAY_BASE_URL = "http://localhost:8000"
$env:STUDIO_RUNTIME_MANAGER_BASE_URL = "http://localhost:8001"
$env:STUDIO_CONTROL_CENTRE_BASE_URL = "http://localhost:8002"
$env:STUDIO_DELIVERY_VALIDATOR_ROOT = "..\ai-delivery-validator"
$env:LOCAL_LLM_BASE_URL = "http://localhost/v1"

uv run uvicorn ai_adoption_studio.main:app --reload --port 8010
```

- Inbox: http://localhost:8010/
- Wizard: http://localhost:8010/wizard/{lead_id} (HTMX requests include internal API key from server-rendered headers)
- Public EOI API: `POST http://localhost:8010/api/v1/eoi`

## Run tests

```powershell
uv run pytest -v
```

Live stack tests: `uv run pytest -v -m live_stack`

## Environment

| Variable | Purpose |
|----------|---------|
| `STUDIO_DATA_ROOT` | Artifact storage root (default `./data`) |
| `STUDIO_INTERNAL_API_KEY` | Operator wizard/API auth |
| `STUDIO_PLATFORM_API_KEY` | Gateway/SDK smoke and validation |
| `STUDIO_GATEWAY_BASE_URL` | Gateway base URL (default `http://localhost:8000`) |
| `STUDIO_RUNTIME_MANAGER_BASE_URL` | RM base URL (default `http://localhost:8001`) |
| `STUDIO_CONTROL_CENTRE_BASE_URL` | Control Centre URL (default `http://localhost:8002`) |
| `STUDIO_DELIVERY_VALIDATOR_ROOT` | Path to ai-delivery-validator |
| `STUDIO_CURSOR_API_KEY` | Cursor agent API key (Phase 4 assist) |
| `STUDIO_CURSOR_WORKSPACE_ROOT` | Parent AI Adoption folder for Cursor local runtime |
| `LOCAL_LLM_BASE_URL` | Internal narrative generation |
