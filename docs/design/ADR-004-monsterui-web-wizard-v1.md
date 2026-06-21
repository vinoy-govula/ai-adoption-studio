# ADR-004 — Operator Web Wizard (FastHTML + MonsterUI)

**Status:** Accepted  
**Date:** 2026-06-21  
**Supersedes:** [ADR-003-console-application.md](./ADR-003-console-application.md)  
**Parent spec:** [ARCH-adoption-studio-wizard-v1.md](./ARCH-adoption-studio-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## Context

ADR-003 proposed a Typer + Textual console application. The operator experience is now required to be a **browser-based wizard** with richer UI/UX while staying on the platform's server-rendered stack.

Control Centre already uses **FastHTML + HTMX + TailwindCSS**. Adoption Studio should match that pattern and adopt **MonsterUI** for pre-built components (forms, cards, modals, steps, markdown preview).

---

## Decision

Adoption Studio **operator experience** is a **FastHTML web application** with MonsterUI:

| Layer | Technology |
|-------|------------|
| App framework | **FastHTML** (`fast_app`, route decorators) |
| Interactivity | **HTMX** (partial swaps, polling, form posts) |
| Components & styling | **MonsterUI** (`Theme`, `Card`, form `Label*`, modals, steps) |
| Public EOI | Same FastAPI/FastHTML process — `POST /api/v1/eoi` |
| Auth | `STUDIO_INTERNAL_API_KEY` on operator routes |

**Not in scope:** Textual TUI, Typer operator wizard, Streamlit, Gradio.

Optional future: thin Typer CLI for CI (`studio export`, `studio validate --lead`) — scripts only, not primary UX.

---

## MonsterUI usage

- Initialize: `fast_app(hdrs=Theme.slate.headers())` (or brand-aligned theme)
- Layout: `Container`, `Grid`, `DivVStack` / spacing helpers
- Wizard: stepper sidebar + `Card` content panels; HTMX for step navigation
- Forms: MonsterUI `LabelInput`, `LabelSelect`, etc. from question-set JSON
- Narrative: `render_md()` for assessment markdown preview
- Cursor assist: MonsterUI modal pattern + HTMX/stream fetch
- Align visual language with Control Centre (sidebar nav, slate/neutral palette)

Reference: [MonsterUI docs](https://monsterui.answer.ai/), [FastHTML concise guide](https://www.fastht.ml/docs/ref/concise_guide.html)

---

## Consequences

**Positive:**
- Richer UX with less custom Tailwind boilerplate
- Platform-consistent with Control Centre (FastHTML + HTMX)
- HTMX polling natural for deploy logs and live status
- Remote operator access via browser (SSH tunnel / VPN)

**Negative:**
- MonsterUI adds dependency and learning curve
- Control Centre does not yet use MonsterUI — Studio may look slightly richer until CC adopts shared theme

**Mitigations:**
- Extract shared theme tokens (colours, sidebar width) for future CC alignment
- Keep business logic in services; pages stay thin

---

## Rejected alternatives

| Alternative | Why rejected |
|-------------|--------------|
| Textual TUI (ADR-003) | Superseded — user chose web + richer UI |
| Raw Tailwind only (current prototype) | Too bland; manual styling burden |
| Streamlit / Gradio | Off-platform paradigm; poor wizard/state fit |
| SPA (React/Vue) | Violates server-rendered MVP rule |

---

## Implementation checklist

- [ ] `pyproject.toml` — add `monsterui`
- [ ] `layouts/base.py` — MonsterUI theme + sidebar shell
- [ ] Replace CDN Tailwind with `Theme.*.headers()` in operator pages
- [ ] Deprecate any Textual/TUI scaffolding if present
- [ ] Update design pack references from ADR-003 to ADR-004

---

**See also:** [SPEC-web-interface-v1.md](./SPEC-web-interface-v1.md), [UX-component-catalog-v1.md](./UX-component-catalog-v1.md)
