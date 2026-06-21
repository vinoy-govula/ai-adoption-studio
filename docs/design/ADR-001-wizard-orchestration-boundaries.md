# ADR-001 — Wizard Orchestration Boundaries

**Status:** Proposed  
**Date:** 2026-06-21  
**Parent spec:** [ARCH-adoption-studio-wizard-v1.md](./ARCH-adoption-studio-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## Context

Operators need to deploy and validate playground stacks from the Adoption Studio UI. Platform boundaries state:

- **Gateway** must not start/stop/deploy runtimes
- **Runtime Manager** owns deployment generation and validation harness
- **Adoption Studio** must not own inference or runtime lifecycle internals

Deliverable Set E also states Studio "must not own runtime deploy" — yet operators require a one-click deploy experience.

---

## Decision

Adoption Studio **orchestrates** deployment and validation through **existing adapters**, never by embedding infrastructure logic:

1. **Kit generation:** Call RM `playground_kit` builder or `ai-delivery-validator` `delivery-generate-kit`
2. **Lab deploy:** Invoke `delivery-deploy-lab` as subprocess with manifest + staging dir
3. **Validation:** Invoke `delivery-validate` / RM `validate_playground.py` with manifest
4. **Status:** Read-only HTTP to Gateway, RM, Control Centre health/metrics endpoints
5. **Inference tests:** Platform SDK only (`AIClient.chat(capability=...)`)

Studio owns: UI, workflow state, job tracking, log presentation, operator approvals.

Studio does **not** own: compose file generation, container lifecycle, capability routing, audit storage.

---

## Consequences

**Positive:**
- Boundary-compliant deploy-from-UI
- Single validation code path (RM + delivery-validator)
- Easier testing via mocked adapters

**Negative:**
- Subprocess overhead; log streaming requires extra work
- Studio depends on sibling repo CLIs being on PATH / uv run

**Mitigations:**
- `DeploymentOrchestrator` adapter with configurable command templates
- Future: optional HTTP service wrapper in delivery-validator (out of v1 scope)

---

## Rejected alternatives

| Alternative | Why rejected |
|-------------|--------------|
| Studio runs `docker compose` directly | Violates RM ownership; duplicates deployment-catalog logic |
| Studio calls Gateway to deploy | Gateway boundary violation |
| Embed validation in Studio | Duplicates `playground.py`; drift risk |

---

## Implementation checklist

- [ ] `adapters/delivery_validator.py` with `generate_kit`, `deploy_lab`, `validate`
- [ ] Config: `STUDIO_DELIVERY_VALIDATOR_UV`, `STUDIO_RM_ROOT`
- [ ] Integration tests mock subprocess

---

**See also:** [SPEC-deployment-orchestration-v1.md](./SPEC-deployment-orchestration-v1.md)
