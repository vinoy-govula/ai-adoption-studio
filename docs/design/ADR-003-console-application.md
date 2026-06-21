# ADR-003 — Operator Console Application (CLI/TUI)

**Status:** Superseded by [ADR-004-monsterui-web-wizard-v1.md](./ADR-004-monsterui-web-wizard-v1.md)  
**Date:** 2026-06-21  
**Parent spec:** [ARCH-adoption-studio-wizard-v1.md](./ARCH-adoption-studio-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## Context

Initial design assumed a server-rendered web wizard (FastHTML + HTMX). The operator tool is intended to run locally on an engineer's workstation as part of lab delivery — a **console application** is a better fit: no browser dependency, native log streaming, and alignment with sibling CLIs (`delivery-*`, `validate_playground.py`).

The existing prototype includes a minimal FastHTML UI and public EOI HTTP API.

---

## Decision

Adoption Studio **operator experience** is a **console application**:

| Layer | Technology |
|-------|------------|
| CLI entry | **Typer** — `studio` command group |
| Interactive wizard | **Textual** TUI — stepper, forms, live panels |
| Formatting | **Rich** — tables, progress, markdown preview |
| Prompts (fallback) | **Questionary** or Typer prompts for non-TUI mode |

**Optional secondary surface:** `studio serve-eoi` retains a minimal FastAPI for public `POST /api/v1/eoi` only (website intake). Operator workflow does **not** use HTTP/HTML.

Remove FastHTML as the operator UI stack (may remain only if `serve-eoi` is implemented in-process).

---

## Consequences

**Positive:**
- Operators stay in terminal alongside deploy/validate CLIs
- Log streaming and job progress are natural in console
- No auth middleware for HTML routes; local OS user + optional `STUDIO_INTERNAL_API_KEY` for EOI serve mode

**Negative:**
- Textual learning curve; Windows terminal compatibility must be tested
- No remote browser access without SSH + terminal

**Mitigations:**
- Support `studio wizard --lead {id} --no-tui` for CI/scripted runs
- Document Windows Terminal / WSL2 requirement

---

## Rejected alternatives

| Alternative | Why rejected |
|-------------|--------------|
| FastHTML web wizard | User requirement: console app |
| Web + console dual parity | Doubles maintenance; console is primary |
| Plain Typer only (no TUI) | Poor live status / log streaming UX |

---

## Implementation checklist

- [ ] `pyproject.toml` — add `typer`, `textual`, `rich`; optional `serve-eoi` extra
- [ ] `src/ai_adoption_studio/cli/` package
- [ ] Entry point: `studio = ai_adoption_studio.cli.main:app`
- [ ] Deprecate FastHTML pages for operator flow

---

**See also:** [ADR-004-monsterui-web-wizard-v1.md](./ADR-004-monsterui-web-wizard-v1.md) (supersedes this ADR)
