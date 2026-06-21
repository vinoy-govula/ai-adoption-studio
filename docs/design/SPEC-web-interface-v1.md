# SPEC — Web Interface (FastHTML + MonsterUI + HTMX) v1

**Status:** Draft for review  
**Parent spec:** [ADR-004-monsterui-web-wizard-v1.md](./ADR-004-monsterui-web-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. Application bootstrap

```python
from fasthtml.common import *
from monsterui.all import *

app, rt = fast_app(
    hdrs=Theme.slate.headers(highlightjs=True),
)
```

Run: `uv run uvicorn ai_adoption_studio.main:app --reload --port 8010`

Dependencies: `python-fasthtml`, `monsterui`, `httpx`, `ai-runtime-manager`

---

## 2. Layout shell

Replace raw Tailwind CDN in `layouts/base.py`:

```python
def page_layout(title: str, active: str, *content: FT) -> FT:
    return Html(
        Head(Title(title), *Theme.slate.headers(highlightjs=True)),
        Body(
            Div(cls="flex min-h-screen")(
                sidebar(active),
                Main(cls="flex-1 p-6")(Container(*content)),
            )
        ),
    )
```

Sidebar: MonsterUI-styled nav matching Control Centre structure (links, active state).

---

## 3. HTML routes

| Method | Path | Step | Handler |
|--------|------|------|---------|
| GET | `/` | inbox | leads list (MonsterUI `Table` or card list) |
| GET | `/wizard/{lead_id}` | current | redirect to current step |
| GET | `/wizard/{lead_id}/{step_id}` | * | wizard step partial |
| POST | `/wizard/{lead_id}/{step_id}` | * | step action |
| POST | `/wizard/{lead_id}/back` | * | go_back |
| POST | `/wizard/{lead_id}/draft` | * | save_draft |
| GET | `/eoi-form` | public demo | dynamic EOI form |
| GET/POST | `/export` | export | pipeline CSV |

Legacy `/leads/{id}` → redirect to `/wizard/{lead_id}`.

---

## 4. JSON / HTMX API routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/eoi` | Public EOI (unchanged) |
| GET | `/api/leads/{id}/status` | StatusSnapshot JSON → StatusGrid partial |
| GET | `/api/leads/{id}/capabilities` | Capability picker options |
| POST | `/api/leads/{id}/smoke-test` | Quick SDK smoke |
| GET | `/api/jobs/{job_id}` | Job status partial |
| GET | `/api/jobs/{job_id}/log?tail=N` | DeployLogViewer partial |
| POST | `/api/leads/{id}/deploy` | Start deploy job |
| POST | `/api/leads/{id}/validate` | Start validate job |
| POST | `/api/leads/{id}/cursor/certify` | Cursor certify |
| POST | `/api/leads/{id}/cursor/troubleshoot` | Stream troubleshoot |
| POST | `/api/leads/{id}/cursor/pir` | PIR draft |
| GET | `/api/leads/{id}/cursor/runs` | Run history partial |
| GET | `/healthz` | Health |

HTMX patterns: `hx-get`, `hx-post`, `hx-target="#step-content"`, `hx-trigger="every 10s"` for polling.

---

## 5. Auth

| Route class | Auth |
|-------------|------|
| Public EOI | Rate limit only |
| Operator wizard | `STUDIO_INTERNAL_API_KEY` header or session cookie |
| JSON API | `Authorization: Bearer {key}` |

---

## 6. Module layout

```text
src/ai_adoption_studio/
  main.py                 # app wiring, register routes
  layouts/base.py         # MonsterUI page_layout, sidebar
  pages/
    inbox.py
    wizard.py             # wizard shell
    wizard_steps/         # one module per step partial
  components/             # MonsterUI + HTMX fragments
  routes/
    api_leads.py
    api_jobs.py
    api_cursor.py
  middleware/auth.py
  services/               # unchanged orchestration layer
  adapters/
```

---

## 7. Optional CI CLI (non-primary)

Thin Typer scripts for automation only — not operator wizard:

```text
studio export pipeline
studio jobs status JOB_ID
```

No Textual. Implemented in Phase 4+ if needed.

---

## 8. Implementation checklist

- [ ] Add `monsterui` to `pyproject.toml`
- [ ] Refactor `layouts/base.py` to MonsterUI theme
- [ ] Split routes from monolithic `main.py`
- [ ] Auth middleware on `/wizard/*` and `/api/leads/*`

---

**See also:** [UX-wizard-flow-v1.md](./UX-wizard-flow-v1.md), [SPEC-wizard-state-model-v1.md](./SPEC-wizard-state-model-v1.md)
