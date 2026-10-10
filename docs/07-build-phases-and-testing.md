# 07 — Build Phases, Exit Criteria, Testing

> Do **not** convert everything at once. Finish and verify each phase before starting the next. Each phase ends with passing tests and a **runnable demo**. When asked to "continue", pick up at the earliest incomplete phase. Commit small, one concern per commit.

---

## 1. Phases

| Phase | Scope | Exit criteria |
|---|---|---|
| **0. Repo prep** | Move handloom code to `legacy/handloom/` (no deletions); scaffold `backend/`, `frontend/`, `configs/`, `docs/`, `Makefile`, `docker-compose.yml`, `.env.example`; fix legacy issues (distinct ports, no `pip install smtplib`, bundled Three.js) | `make up` starts Postgres; `make lint` / `make test` run (empty but green); legacy files untouched apart from move |
| **1. Foundation** | Postgres + Alembic + FastAPI skeleton; `catalog.yaml` / `factory.yaml` loaders; departments, workstation types/workstations, skills, component types, prerequisites DAG, loom models, materials/BOM | `make migrate && make seed` loads 5 depts, ~35 workstations, 31 component types; DAG acyclic check passes; `GET /departments`, `GET /component-types` work; eligibility query returns correct workstation types/workstations/qualified workers |
| **2. Workforce & shifts** | Workers, skills, roster, availability, calendar, shift utility (single source of shift math), loan/overtime plan rows | Roster for any date/shift returns correct present/absent/loan counts; `max_h/day` and 1-shift/day rules enforced by tests; skill-coverage query correct |
| **3. Orders & tracking** | Orders → loom units → component units; `component_event` + `apply_event()` projection; state machine; readiness (prereq DAG); kit status; loom progress; manual event endpoint | Create order of N looms ⇒ N×32 units; illegal transitions → 409; `rebuild_projection()` ≡ live; dept/loom progress formulas tested; `GET /looms/{serial}` returns stage ribbon + blocking component |
| **4. Synthetic data + SimPy** | Generator (L1–L8), scenarios A–G, validation script, shared SimPy engine, loader, live driver | 6-month dataset generates deterministically; **validation script passes**; scenario signatures asserted; live driver streams events to API |
| **5. Capacity / load / root cause (+ baseline predictions)** | Capacity engine (per dept/workstation/skill-pool, shift/day/week), Monte-Carlo workload, load classification, bottleneck, root cause, throughput (looms/day), baseline build-time predictor, capacity forecast | Boundary tests 69.9/70/95/95.1 pass; zero-capacity returns `UNAVAILABLE`; `P90(agg) < ΣP90`; example E1 (SENS underload cause) reproduced; `GET /departments/{code}/snapshot` fully populated |
| **6. 3D twin UI** | Factory scene (5 pods, flow lanes, kit buffers, load towers, progress rings), department view (component board, tiles via visual registry), side-panel tabs (Overview/Capacity/Load/Prediction/Workforce/Balancing), loom pipeline strip + Trace mode, `/looms/[serial]` passport, status language, a11y | E2E flow: `/twin` → click pod → tiles + panel populated from API → tile drawer → trace a loom; keyboard-only works; reduced-motion respected; 60 fps smoke; no colour-only status |
| **7. ML prediction** | LightGBM quantile build-time models, Holt-Winters workload forecasts (7/30/90 d), Monte-Carlo loom completion, backtests | Time-split backtest; P75/P90 coverage ≈ 75/90 on holdout; **beats baseline**; leakage test passes; quantiles monotone; cold-start fallback flagged |
| **8. Load balancing + optimizer + what-if** | `validate_assignment()` (V1–V8), recommendation generator, CP-SAT scheduler + independent feasibility checker, what-if engine (BEFORE/AFTER/DELTA), simulation controls & injection, Apply (plan-only) | Examples E1/E2/E3 reproduced; infeasible input returns diagnosis; solver output passes independent checker; sim never writes live tables; Apply writes plan rows with audit |
| **9. Monitoring, alerts, terminal** | Metrics (overall + per-dept + per load segment), drift (PSI/KS), retraining recommendation, champion/challenger, rollback, alerts + email, `/terminal/[dept]`, optional MLflow | Scenario G ⇒ drift flag ⇒ coverage drop ⇒ retrain recommended ⇒ challenger evaluated ⇒ promote/reject recorded; regression-test degraded model triggers alert; terminal event updates twin live via WS |
| **10. Integration** | Full SENSE→PREDICT→DECIDE→EXECUTE→LEARN loop, pipeline page, docs polish, demo script | All eight planner questions (root `CLAUDE.md` §3) answerable end-to-end in the demo; `make test` and `make lint` clean |

**Dependency note:** the generator (Phase 4) uses SimPy; the capacity engine (Phase 5) is used for labels. Build a *minimal* SimPy core in Phase 4 and the capacity math in Phase 5 in lockstep; labels (L7) are produced after Phase 5 lands (a re-run of `synthetic.load --labels`). A frontend shell may start after Phase 3 against seeded data, but **do not** build the 3D scene before data model, state machine and capacity engine exist.

---

## 2. Testing requirements

### 2.1 Unit
- State machine: exhaustive legal/illegal transition table.
- Progress formulas (hours-weighted dept/loom progress; counts per status sum to total).
- Shift/calendar utility: shift boundaries, breaks, holiday, overtime caps, cross-midnight handling.
- Eligibility: component → workstation type → workstation; skill level + certification validity.
- Capacity math: each layer; skill-pool binding; `min(workstation, labour)`; **zero capacity**.
- Load classification boundaries: **69.9 / 70 / 95 / 95.1**, risk-quantile switch (`p75`→`p90`) via config.
- Quantile monotonicity (P50 ≤ P75 ≤ P90) after post-processing.
- Monte-Carlo aggregation: determinism with seed; `P90(agg) < ΣP90(units)`.
- Throughput: system throughput = min over depts; no cross-dept summing.

### 2.2 Property / consistency
- Dept capacity = Σ its workstations/pools (no double counting); loans reduce home capacity and add to host capacity by the same hours.
- `rebuild_projection()` ≡ live projection (random event sequences).
- Prerequisite DAG: no unit starts before prerequisites complete.
- No worker/workstation double-booking in any generated or solved schedule.

### 2.3 Scheduler & balancing
- **Independent feasibility checker** re-verifies every hard constraint on solver output.
- Infeasible inputs return a **diagnosis** naming the blocking constraint group.
- `validate_assignment()` rejects each of V1–V8 with a targeted test (skill too low, expired cert, workstation ineligible/down, overtime cap, material missing, prereq not done, capacity exceeded, crew unmet, double-booking, loan strands home dept).
- No recommendation is emitted unless all checks pass (negative tests).
- E1/E2/E3 worked examples (docs/03 §4.3).

### 2.4 ML
- Time-based split only; leakage test; coverage test for P75/P90; metrics per dept and per load segment; baseline-beating test; cold-start fallback; degraded-model ⇒ monitoring alert; challenger regressing on OVERLOAD segment or bottleneck dept ⇒ **no auto-promote**.

### 2.5 Simulation / sandbox
- Same `(snapshot, seed, events)` ⇒ identical output.
- **DB diff test:** running any sim/what-if/recommendation-simulate leaves live tables unchanged.
- Event injection scenarios each produce their expected signature.

### 2.6 Synthetic data
- `validate` suite (docs/06 §10) as a pytest integration test; scenarios A–G signatures; determinism (byte-identical rerun); `gt_*` columns absent from feature lists.

### 2.7 API
- Contract tests against OpenAPI; role gating; idempotent ingest; error shape; no NaN/Infinity in payloads; snapshot schema; WS `seq` monotonic.

### 2.8 Frontend
- See `docs/04` §9 (Vitest + Playwright, a11y checks including `axe` on key pages, keyboard-only flow, reduced-motion).

### 2.9 Scenarios (integration)
Each of A–G has an integration test asserting its expected signature end-to-end (data → engines → API payload).

---

## 3. Demo script (Phase 10 acceptance)

1. Start stack; open `/twin` — five pods, load towers, badges (text), kit buffers, pipeline strip.
2. Click **Fabrics** — component board (6 tiles), panel: capacity, Expected/P75/P90 load, predictions, workers & shifts.
3. Click `FAB-HEDDLE` tile — unit table, planned vs actual, blocked reasons.
4. Trace loom `LM100-0001xx` — see its state across all five departments; open passport; read predicted completion and on-time probability.
5. Inject **worker absence** in sandbox (SENS, `SK-SOLDER≥3`) — watch SENS load rise, `ASY-SENSOR` starve; see recommendations with V1–V8 checks; simulate; **Apply** (plan-only).
6. Switch to scenario **G** data — monitoring shows drift, coverage drop, retraining recommendation; run challenger; promotion decision recorded.
7. Answer the eight planner questions from the UI.

---

## 4. Definition of done (every task)

1. Respects root `CLAUDE.md` §4 rules.
2. Tests added/updated and passing; `make lint` clean (ruff, mypy, eslint, `tsc --noEmit`).
3. No hard-coded catalog, thresholds, shifts, headcounts, layout coordinates.
4. Explainable outputs carry Problem/Cause/Evidence/Confidence/Action/Impact.
5. Docs updated; Alembic migration for schema changes; OpenAPI regenerated and frontend types refreshed.
6. UI: keyboard reachable, status not colour-only, reduced-motion honoured, no console errors.
7. Small, single-concern commits.

---

## 5. Open questions (ask the user; defaults already set in root §13)

- Real component lists per department (confirm or edit `catalog.yaml`).
- Real headcount, shift pattern (days/shifts/overtime rules), and loan policy between departments.
- Number and mix of loom models; typical order sizes and volumes.
- Auth/roles and identity provider; privacy rules for worker names.
- Source of real data later (barcode/RFID/MES/ERP) and deployment target (on-prem vs cloud; air-gap?).
- Whether MLflow and FIWARE are wanted at all in v1.
