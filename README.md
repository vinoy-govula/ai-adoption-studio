# AI Adoption Studio

Internal operator **web wizard** for EOI intake, AI readiness assessment, playground deploy, validation, and pipeline CSV export.

Operator docs and question sets: [docs/README.md](docs/README.md). **Wizard design pack:** [docs/design/README.md](docs/design/README.md) (FastHTML + MonsterUI + HTMX). JSON schemas and engine specs: [ai-runtime-manager/docs/adoption-studio](../ai-runtime-manager/docs/adoption-studio/README.md).

## Prerequisites

Requires [uv](https://docs.astral.sh/uv/), [Docker](https://docs.docker.com/) and Python 3.13. Sibling checkouts of [ai-gateway](../ai-gateway), [ai-runtime-manager](../ai-runtime-manager), [ai-platform-sdk](../ai-platform-sdk), [ai-delivery-validator](../ai-delivery-validator) and [deployment-catalog](../deployment-catalog) are required (path dependencies and dependency stack).

## Quick start — one command

From the **`AI Adoption/` workspace root** (the parent folder containing all repos):

```powershell
.\studio.ps1 up
```

`studio up` verifies prerequisites, creates `ai-adoption-studio/.env` once from `.env.example` (generate-once, reuse-every-time), starts the dependency stack (Gateway DB, Runtime Manager DB, Runtime Manager, Control Centre) via `deployment-catalog` compose, waits for health, then launches Studio.

| Command | Effect |
|---------|--------|
| `.\studio.ps1 up` | Ensure config → start deps → wait for health → start Studio |
| `.\studio.ps1 down` | Stop the dependency stack |
| `.\studio.ps1 status` | Print health of each layer + Studio |
| `.\studio.ps1 logs` | Tail dependency logs |

Other shells: `studio.bat up` (cmd) or `./studio up` (bash/pwsh on macOS/Linux).

> **Stable Gateway key.** For "generate once, reuse every time", enable the Gateway startup seed (see [ai-gateway/README.md](../ai-gateway/README.md) → *Persistent bootstrap key* and [Gateway ADR-006](../ai-gateway/docs/adr/ADR-006-startup-bootstrap-key-seed.md)) and set the same value as `STUDIO_PLATFORM_API_KEY` in `.env`. This removes the ephemeral-key copy-paste loop.

Once up:

- Inbox: http://localhost:8010/
- Wizard: http://localhost:8010/wizard/{lead_id} (HTMX requests include internal API key from server-rendered headers)
- Public EOI API: `POST http://localhost:8010/api/v1/eoi`

See the design docs: [SPEC-operator-single-command-v1.md](docs/design/SPEC-operator-single-command-v1.md), [ADR-005](docs/design/ADR-005-operator-startup-and-console.md), [PLAN-operator-experience-v1.md](docs/design/PLAN-operator-experience-v1.md).

## Manual start (advanced / debugging)

To run Studio alone against an already-running stack (see [deployment-catalog/README.md](../deployment-catalog/README.md)):

```powershell
cd ai-adoption-studio
uv venv --python 3.13
uv sync --extra dev
copy .env.example .env   # then edit values
uv run uvicorn ai_adoption_studio.main:app --reload --port 8010
```

`config.py` loads `.env` automatically (prefix `STUDIO_`), so environment values need not be exported by hand.

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
| `STUDIO_DEPLOYMENT_CATALOG_ROOT` | Path to deployment-catalog |
| `STUDIO_PORT` | Studio server port (default `8010`) |
| `STUDIO_CURSOR_API_KEY` | Cursor agent API key (Phase 4 assist) |
| `STUDIO_CURSOR_WORKSPACE_ROOT` | Parent AI Adoption folder for Cursor local runtime |
| `LOCAL_LLM_BASE_URL` | Internal narrative generation |

Values are read from `ai-adoption-studio/.env` (created once by `studio up`). Copy from [.env.example](.env.example).
