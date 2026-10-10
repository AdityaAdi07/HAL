# 05 — API, Realtime, Ingestion, Jobs, Roles, Alerts

> Prefix `/api`. Typed Pydantic v2 responses, paginated lists (`?page&page_size` or cursor), consistent error shape `{code, message, details}`. OpenAPI is the contract; frontend types are generated from it. Contract tests run against the schema.

---

## 1. REST surface

```
Departments   GET  /departments                       list + live summary (load class, progress, status)
              GET  /departments/{code}                 master data
              GET  /departments/{code}/snapshot        ← the payload the 3D dept panel needs (§2)
              GET  /departments/{code}/components      component board: per-type summary
              GET  /departments/{code}/workforce?window=current|next|today|tomorrow|week
              GET  /departments/{code}/workstations

Components    GET  /component-types                    catalog (+ prerequisites graph)
              GET  /component-types/{code}
              GET  /component-units                    filters: dept, type, loom, status, shift, order, late
              GET  /component-units/{id}               + /events
              POST /component-units/{id}/events        report event (terminal/manual) — role-gated

Looms/Orders  GET  /orders        POST /orders         create loom build order (planner)
              GET  /orders/{code}
              GET  /looms                              filters: order, model, stage, status, late
              GET  /looms/{serial}                     passport: stage ribbon, components, critical path
              GET  /looms/{serial}/prediction

Workforce     GET  /workers  GET /workers/{code}       skills, availability
              GET  /roster?from&to&dept                POST /roster/loan (creates plan row via recommendation apply)
              GET  /shifts   GET /calendar

Capacity      GET  /capacity                           all depts, current/today/week + throughput (looms/day)
              GET  /capacity/departments/{code}?window=SHIFT|DAY|WEEK
              GET  /capacity/workstations
              GET  /capacity/forecast?scope&horizon=7|30|90

Load          GET  /load                               Expected/P75/P90 per dept + class + rule_fired
              GET  /load/departments/{code}
              GET  /bottlenecks
              GET  /root-cause?scope=dept:DEPT-SENS

Forecast      GET  /forecast/workload?level=factory|dept|component&id&horizon
              POST /forecast/predict                   ad-hoc (async job)

Balancing     GET  /recommendations?status&dept        list
              GET  /recommendations/{id}
              POST /recommendations/generate           async job → job_id
              POST /recommendations/{id}/simulate      async job (sandbox)
              POST /recommendations/{id}/apply         role-gated, audited, writes PLAN only
              POST /recommendations/{id}/dismiss

Optimization  POST /optimization/schedule              async job → job_id
              GET  /optimization/schedule/{id}         status, solver_status, gap, objective, changed_assignments

What-if       POST /what-if/run                        body: scenario + params → job_id
              GET  /what-if/{id}                       before/after/delta + recommended action

Simulation    POST /sim/sessions                       create from snapshot (seed)
              POST /sim/sessions/{id}/start|pause|reset|advance   (+1 hour | +1 shift | +1 day)
              POST /sim/sessions/{id}/events           inject: worker_absence, material_shortage, workstation_breakdown,
                                                        demand_spike, urgent_order, time_inflation, rework_surge, restore_normal
              GET  /sim/sessions/{id}/state
Live driver   POST /live/start|pause|speed             synthetic replay driver (demo/live mode)

Materials     GET  /materials  /materials/requirements  /materials/shortages

Models        GET  /models  /models/health
              POST /models/retrain|promote|reject|rollback
Alerts        GET  /alerts  POST /alerts/{id}/ack   GET/PUT /alerts/config (thresholds, email)
Jobs          GET  /jobs/{id}
Ingest        POST /ingest/component-events          batch adapter endpoint (§5)
Admin         GET  /health  GET /config   POST /seed/reload (dev only)
WebSocket     /ws                                     §3
```

Long-running work (CP-SAT, SimPy what-if, Monte-Carlo loom prediction, retraining) returns `{job_id}` immediately; clients poll `GET /jobs/{id}` (or receive `job.completed` over WS). CPU-bound work runs in a **process pool**, never on the event loop.

---

## 2. `GET /departments/{code}/snapshot` — contract for the department panel

Single call, cache-friendly (`as_of` + ETag), assembled by `services/`, computed by pure engines.

```json
{
  "dept": {"code": "DEPT-FAB", "no": 2, "name": "Fabrics"},
  "as_of": "2026-10-07T09:14:00Z",
  "data_source": "SYNTHETIC",
  "shift": {"id": "SHIFT-A", "start": "06:00", "end": "14:00", "ends_in_min": 166},

  "status": {
    "load_class": "OVERLOAD_RISK",
    "rule_fired": "R2_EXPECTED_HEALTHY_P75_OVER",
    "flags": ["SKILL_BOUND"],
    "is_system_bottleneck": false
  },

  "capacity": {
    "unit": "hours",
    "current_shift": {"theoretical": 96.0, "scheduled": 96.0, "available": 88.0, "labour": 45.0, "usable": 33.8, "efficiency": 0.86, "material_factor": 0.98},
    "today":         {"theoretical": 192.0, "scheduled": 192.0, "available": 176.0, "labour": 90.0, "usable": 67.5, "efficiency": 0.86, "material_factor": 0.98},
    "week":          {"usable": 338.0},
    "throughput_looms_per_day": 5.5,
    "predicted": [
      {"horizon_days": 7,  "expected_h": 338.0, "pessimistic_h": 301.0},
      {"horizon_days": 30, "expected_h": 1440.0, "pessimistic_h": 1290.0}
    ]
  },

  "load": {
    "horizon_days": 7,
    "workload_h": {"expected": 296.0, "p75": 326.0, "p90": 352.0},
    "load_pct": {"expected": 88.0, "p75": 96.9, "p90": 104.2},
    "stress_load_pct": 116.9,
    "capacity_balance_h": -42.0,
    "thresholds": {"under": 70, "over": 95, "risk_quantile": "p75"}
  },

  "progress": {"hours_weighted_pct": 61.4, "units_done": 74, "units_total": 120, "wip": {"in_progress": 6, "queued": 11, "in_qc": 2, "blocked": 1}},

  "components": [
    {
      "code": "FAB-HEDDLE", "name": "Heddle frame set", "visual_key": "heddle_frames",
      "counts": {"done": 14, "in_progress": 2, "queued": 3, "in_qc": 1, "blocked": 0, "rework": 0, "total": 20},
      "progress_pct": 78.0, "dominant_status": "IN_PROGRESS",
      "predicted_finish": {"expected": "2026-10-09T11:30Z", "p75": "2026-10-09T15:00Z", "p90": "2026-10-10T08:00Z"},
      "std_h": 3.0, "actual_avg_h": 3.3, "workstations": ["HRJ-01", "HRJ-02"], "block_reasons": []
    }
  ],

  "workforce": {
    "window": "current",
    "rostered": 6, "present": 5, "absent": 1, "loans_in": 0, "loans_out": 1,
    "skill_coverage": [{"skill": "SK-PRECISION", "min_level": 3, "required": 2, "qualified_present": 2}],
    "workers": [
      {"code": "W-FAB-03", "availability": "PRESENT", "roster_kind": "REGULAR", "workstation": "HRJ-02",
       "component_unit": "LM100-000118/FAB-HEDDLE", "skills": [{"skill": "SK-PRECISION", "level": 4}], "utilisation_pct": 91}
    ],
    "timeline_url": "/api/departments/DEPT-FAB/workforce?window=today"
  },

  "prediction": {
    "workload_forecast": {"method": "holt_winters_trend_only", "note": "history < 2 seasonal cycles", "horizon_days": 30, "series_url": "/api/forecast/workload?level=dept&id=DEPT-FAB&horizon=30"},
    "next_looms": [{"serial": "LM100-000118", "complete": {"expected": "...", "p75": "...", "p90": "..."}, "on_time_prob": 0.82}],
    "model": {"name": "build_time", "version": "v3", "champion": true, "p75_coverage": 0.74, "p90_coverage": 0.91}
  },

  "root_cause": {"problem": "...", "cause": "TIME_INFLATION", "evidence": {}, "confidence": 0.74, "recommended_action": {}, "expected_impact": {}},
  "recommendations": [{"id": "rec_123", "type": "OVERTIME", "status": "VALIDATED", "checks": {"V1": true, "V2": true, "V3": true, "V4": true, "V5": true, "V6": true, "V7": true, "V8": true}}]
}
```

Every number in a response is computed from DB/engine output (never constants). Missing predictions are `null` with a `reason`, not omitted silently.

---

## 3. WebSocket `/ws`

- One connection per client; subscribe by scope: `{"action":"subscribe","topics":["dept:DEPT-FAB","factory","alerts","sim:<id>"]}`.
- Server pushes **events, not full-state polling**. Envelope: `{ "type", "ts", "scope", "seq", "data" }`. `seq` is monotonic per topic so the client can detect gaps and refetch a snapshot.
- Event types: `component.status_changed`, `component.progress`, `loom.stage_changed`, `dept.metrics_updated` (throttled ≤ 1/s per dept), `workforce.shift_changed`, `worker.availability_changed`, `workstation.status_changed`, `alert.raised`, `alert.resolved`, `recommendation.created`, `job.completed`, `sim.clock`.
- Heartbeat/ping; client auto-reconnect with backoff; on reconnect resubscribe and refetch snapshots.
- Simulation topics carry `sim:<session_id>` and are **never** mixed with live topics.

---

## 4. Roles and mutation rules

| Role | Can |
|---|---|
| `viewer` | Read everything (worker names masked) |
| `dept_lead` | Report component events for own dept (`/terminal`), acknowledge alerts |
| `supervisor` | + see worker names, run what-if/simulation, dismiss recommendations |
| `planner` | + create orders, generate/apply recommendations, run optimization, change thresholds/config |

Endpoints that write: `POST /orders`, `POST /component-units/{id}/events`, `/recommendations/{id}/apply`, `/alerts/config`, `/ingest/*`, `/models/*`. **Apply** requires `planner`, a confirmation payload, and an audit row. Auth provider is an open question — implement a pluggable dependency (`get_current_user`) with a dev stub; **do not** hard-code a provider.

---

## 5. Ingestion adapter interface (design now, implement real sources later)

```python
class ProductionEventSource(Protocol):
    def stream(self) -> Iterator[ComponentEventIn]: ...      # RFID / barcode / MES / ERP / tablet
```
- `POST /ingest/component-events` accepts batches of `ComponentEventIn` (idempotent via `external_event_id`), validates against the state machine, applies through the same `apply_event()` used everywhere.
- Rejected events (illegal transition, unknown unit) go to a dead-letter table with the reason — never silently dropped.
- Initial sources: (1) **synthetic live driver**, (2) **manual terminal** (`/terminal/[dept]`). Future: barcode/RFID scanner, MES, ERP.

---

## 6. Alerts (adapted from the handloom alert system)

Types: `DEPT_OVERLOAD`, `DEPT_OVERLOAD_RISK`, `DEPT_UNDERLOAD`, `BOTTLENECK`, `COMPONENT_BLOCKED`, `MATERIAL_SHORTAGE`, `WORKER_SHORTAGE`, `SKILL_SHORTAGE`, `WORKSTATION_DOWN`, `LATE_LOOM_RISK`, `HIGH_WIP`, `REWORK_SURGE`, `STARVATION`, `MODEL_DRIFT`, `MODEL_DEGRADATION`, `RETRAINING_REQUIRED`.

- Rules fire from engine outputs with **configurable thresholds**, hysteresis (don't flap), and dedupe window.
- Each alert: `severity` (`INFO|WARN|CRITICAL`), scope, message, `evidence_json` (real numbers), `raised_at`, ack/resolved.
- **Email** notifications (kept from handloom): SMTP creds from env only; per-type opt-in; rate-limited; digest option.
- UI never shows severity by colour alone (icon + text).

---

## 7. Config & cross-cutting

- **No hard-coded** routes, thresholds, shift numbers, weights: `GET /config` exposes effective config (read-only) for the UI.
- Structured request logs with `request_id`; solver/model logs include `model_version`, `scenario_or_session_id`, `solver_status`.
- Pagination limits enforced; consistent `404/409/422` with `{code,message,details}`; idempotency keys on mutating POSTs that create orders/events.
- Rate-limit `/optimization/*`, `/what-if/*`, `/sim/*` per user; cap concurrent jobs.
- Time: all payloads ISO-8601 UTC; clients convert with `FACTORY_TZ`.

---

## 8. API tests

- Contract: every route validates against OpenAPI; snapshot payload matches schema; no `NaN`/`Infinity` in JSON (guard).
- Behavioural: illegal state transitions → `409`; `apply` without role → `403`; sim session event never changes live rows (DB diff test); `ingest` idempotent on repeated `external_event_id`; WS `seq` gaps trigger refetch (frontend test); snapshot for a department with zero usable capacity returns `load_class=UNAVAILABLE`, `load_pct=null`.
