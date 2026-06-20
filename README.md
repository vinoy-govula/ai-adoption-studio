# AI Adoption Studio

Internal operator tool for EOI intake, AI readiness assessment, checkpoint workflow, and pipeline CSV export.

## Quick start

```bash
cd ai-adoption-studio
pip install -e ".[dev]"
pip install -e ../ai-runtime-manager

set STUDIO_DATA_ROOT=./data
set STUDIO_INTERNAL_API_KEY=dev-key
set LOCAL_LLM_BASE_URL=http://localhost/v1

uvicorn ai_adoption_studio.main:app --reload --port 8010
```

- Internal UI: http://localhost:8010/
- Public EOI API: `POST http://localhost:8010/api/v1/eoi`

## Environment

| Variable | Purpose |
|----------|---------|
| `STUDIO_DATA_ROOT` | Artifact storage root (default `./data`) |
| `STUDIO_INTERNAL_API_KEY` | Internal API/UI auth key |
| `LOCAL_LLM_BASE_URL` | Internal narrative generation |
