# SPEC — Live Status Aggregation v1

**Status:** Draft for review  
**Parent spec:** [ARCH-adoption-studio-wizard-v1.md](./ARCH-adoption-studio-wizard-v1.md)  
**Repository owner:** `ai-adoption-studio`

---

## 1. Purpose

Aggregate read-only health signals from Runtime, Gateway, Control Centre, and SDK into a unified view model for the StatusGrid MonsterUI component.

---

## 2. StatusSnapshot view model

```json
{
  "polled_at": "2026-06-21T10:00:00Z",
  "overall": "healthy|degraded|unhealthy|unknown",
  "layers": {
    "runtime": { "status": "healthy", "summary": "...", "details": {} },
    "gateway": { "status": "healthy", "summary": "...", "details": {} },
    "control_centre": { "status": "healthy", "summary": "...", "details": {} },
    "sdk": { "status": "unknown", "summary": "No smoke run yet", "details": {} }
  },
  "errors": []
}
```

---

## 3. Signal catalog

### Runtime (via RM)

| Signal | Source | Notes |
|--------|--------|-------|
| RM API health | `GET {RM}/healthz` | — |
| Deployment status | RM deployment API if available | Optional v1 |
| Preset / profile | From manifest `deployment.preset` | Static from artifact |
| Model loaded | Gateway models or RM validate | Best-effort |

### Gateway

| Signal | Source |
|--------|--------|
| Health | `GET {GW}/healthz` |
| Capabilities count | `GET {GW}/api/v1/capabilities` (service key) |
| Rate limit | From manifest or metrics |
| Metrics snapshot | `GET {GW}/api/v1/metrics` if exposed |

### Control Centre

| Signal | Source |
|--------|--------|
| Health | `GET {CC}/healthz` |
| Deep link | `{CC}/` for manual checks |

### SDK

| Signal | Source |
|--------|--------|
| Last smoke | `workflow-state.validation.last_smoke_result` |
| On-demand | POST smoke-test endpoint |

---

## 4. StatusAggregator service

```python
class StatusAggregator:
    async def poll(self, lead_id: str, *, manifest: dict) -> StatusSnapshot: ...
```

- Parallel `httpx` requests with 5s timeout
- Cache last good snapshot per lead (60s TTL)
- `overall`: unhealthy if Gateway down; degraded if any layer unhealthy

---

## 5. Polling in web UI

| Mechanism | Behaviour |
|-----------|-----------|
| HTMX `hx-get="/api/leads/{id}/status"` + `every 10s` | StatusGrid auto-refresh on live_status step |
| Manual refresh | MonsterUI Button triggers immediate poll |
| BFF | `GET /api/leads/{id}/status` returns HTML fragment or JSON |

---

## 6. Staleness

If 3 consecutive polls fail:

- Show yellow "degraded — cached data"
- Display `polled_at` timestamp
- Retry button

---

## 7. Manifest-derived context

From `playground-kit.manifest.json`:

- `access.public_url` — Gateway base for polls
- `deployment.preset` — Runtime row label
- `deployment.rate_limit` — Gateway row detail
- `client.display_name` — wizard page title

---

## 8. Implementation checklist

- [ ] `adapters/gateway_client.py`
- [ ] `adapters/runtime_manager_client.py`
- [ ] `adapters/control_centre_client.py`
- [ ] `components/status_grid.py`
- [ ] `GET /api/leads/{id}/status` route
- [ ] `services/status_aggregator.py`

---

**See also:** [validation-suite-spec-v1.md](../../ai-runtime-manager/docs/adoption-studio/validation-suite-spec-v1.md), [deployment-catalog README](../../deployment-catalog/README.md)
