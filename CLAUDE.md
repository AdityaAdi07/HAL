# CLAUDE.md — Powerloom Manufacturing Digital Twin (5-Department Factory)

> Master instruction file for AI coding agents (Claude Code / Antigravity).
> Read this fully first, then read the doc in §8 that matches the area you are working on.
> When this file conflicts with an assumption you were about to make, **this file wins**.

---

## 0. Mission

Convert the existing **Handloom / Powerloom Digital Twin** (`AdityaAdi07/Handloom-Main-SDG-9-Winners`, which *monitors one operating loom*) into a:

> **Powerloom Manufacturing Digital Twin — Component Tracking + Capacity & Load Intelligence + Load Balancing + Loom Build Tracking**

### 0.1 The key reframing (read twice)

The old twin showed **a loom running**. The new twin shows **a factory that manufactures looms**.

- The **product** is a powerloom. Each loom is built from ~32 **components**.
- Components are produced by **five departments** (each department owns a set of components).
- The 3D twin is a *view of state*, **not an animation of the build process**. Clicking a department shows **which components it is building and their status, progress, capacity, load, predictions and worker shifts** — never a motion-picture of someone assembling something.
- The intelligence (capacity, load, prediction, balancing) is the product. The 3D scene is its visual layer.

### 0.2 What the user asked for (acceptance summary)

| # | Capability | Meaning |
|---|---|---|
| 1 | **Component tracking** | Every component unit of every loom has a status, progress %, owner dept, workstation, worker, planned vs actual, and predicted finish |
| 2 | **Loom build tracking** | Every loom unit (serial) shows hours-weighted progress, which components are done/late/blocked, current stage, predicted completion date |
| 3 | **Current capacity** | Per department (and workstation/worker): theoretical → scheduled → available → usable capacity for this shift / today / this week |
| 4 | **Predicted capacity** | Capacity forecast (7/30/90 days) from roster, absences, calendar, maintenance |
| 5 | **Load** | Expected / P75 / P90 load % per department with UNDERLOAD / HEALTHY / OVERLOAD / OVERLOAD_RISK + root cause |
| 6 | **Load balancing** | Concrete, validated actions: reassign task, lend worker across depts, add shift/overtime, re-sequence, pace loom release |
| 7 | **Prediction** | Component build-time quantiles, workload forecast, loom completion date distribution, on-time probability |
| 8 | **3D digital twin of 5 departments** | Click a department → component board + status/progress/capacity/load/prediction/workers/shifts |

---

## 1. Relationship to other documents

- If `CLAUDE_5_.md` (the **HAL Manufacturing Digital Twin** spec) exists in the repo, treat it as a **reference for engineering patterns only**: Expected/P75/P90 uncertainty, explainability schema, CP-SAT + SimPy usage, sandbox isolation, monitoring/champion-challenger, anti-patterns for synthetic data. **Do not** import its domain (CNC machines, work centers, parts, routings, SPM/QPH). Where it differs from this file, **this file wins**.
- The legacy handloom code is **archived, not deleted** in the first commit (see §7).

---

## 2. The five departments (fixed)

| No. | Code | Name | Owns | Notes |
|---|---|---|---|---|
| 1 | `DEPT-MECH` | **Mechatronics** | Loom **chain drive and motor** | Drive motor, motor driver, chain, sprockets, tensioner, coupling/mount |
| 2 | `DEPT-FAB` | **Fabrics** | Loom **thread and fibre path** | Warp beam, cloth beam, heddle frames, reed, thread guides, weft holders |
| 3 | `DEPT-SENS` | **Sensors** | Loom **sensors** | Temperature, humidity, RPM, **MPU6050**, **load sensors**, sensor hub |
| 4 | `DEPT-PWR` | **Power Optimization & Inlet** | Power inlet + power optimization | Inlet/protection panel, PSU, energy meter, optimization controller, harness |
| 5 | `DEPT-ASSY` | **Assembly & Integration** | Final assembly of everything | Consumes Depts 1–4 output; frame, integration, calibration, test, packing |

Depts 1–4 are **parallel feeders**. Dept 5 is **gated** by them through a precedence graph (a DAG over component types). The full component catalog, prerequisites, skills and workstations are in `docs/01-domain-departments-components.md`. The catalog is **data (`configs/catalog.yaml`), never hard-coded**.

> The component lists inside each department are **sensible defaults inferred from the one-line descriptions**. They must live in `catalog.yaml` so the user can edit them without code changes. See §13.

---

## 3. Questions the system must answer (planner's questions)

If a feature does not serve one of these, it is low priority.

1. Can we deliver the upcoming loom orders on time? (YES/NO + probability)
2. **Which department** is the problem, and which component types inside it?
3. **Why?** (root cause with evidence + confidence)
4. **What should I do?** (move task, lend worker, add shift, re-sequence, pace release)
5. **Will it work?** (CP-SAT feasibility + SimPy validation of the recommendation)
6. **Where is loom #L-0042 right now**, what is it waiting for, and when will it finish?
7. **Who is working** in each department this shift and the next?
8. **Is the prediction model still reliable?** (monitoring, drift, retraining)

The system runs this loop continuously:

```
SENSE → UNDERSTAND → PREDICT → EXPLAIN → DECIDE → OPTIMIZE → SIMULATE → EXECUTE → LEARN → SENSE
```

---

## 4. Non-negotiable rules

Encode these in code **and tests**, not only comments.

1. **Eligibility chain.** `ComponentType → eligible WorkstationType → Workstation` AND `ComponentType → required Skill (min level) → qualified Worker`. Never assign work because capacity is free. Every assignment (scheduler, what-if, recommendation, simulation) passes the same shared `validate_assignment()` function.
2. **Assignment validity = all of:** skill ✓, workstation ✓, shift/hours ✓, material ✓, prerequisites ✓, capacity ✓. A recommendation failing any check is **never emitted**.
3. **No hard-coded component lists, routes, thresholds, shift lengths, department sizes.** Read from `catalog.yaml` / config / DB.
4. **Thresholds are configurable** per department. Defaults: `<70%` UNDERLOAD, `70–95%` HEALTHY, `>95%` OVERLOAD (95 inclusive = healthy). Do not present them as industry standards.
5. **Underload is a first-class problem**, with its own root-cause analysis (e.g. starved by a bottleneck elsewhere).
6. **Uncertainty everywhere.** Build time, workload, and completion date are always **Expected / P75 / P90**. Never one number. Never *sum P90s* to get an aggregate P90 — aggregate by Monte Carlo (see `docs/03`).
7. **Do not sum capacity across departments.** Departments are not interchangeable pools. Factory throughput = **min over departments** (looms/day). Show per-department load, not a fake factory average.
8. **Explainability.** Every load class, bottleneck and recommendation carries: `Problem, Cause, Evidence, Confidence, Recommended Action, Expected Impact`. Evidence = real numbers from DB/engines, not templated prose.
9. **Events are the truth for status.** `ComponentEvent` is append-only. Component status/progress are derived from events (or a projection kept in sync transactionally). Never overwrite history.
10. **Simulation / what-if never mutate live tables.** They run on a snapshot/sandbox session. Only an explicit, audited **Apply** action changes *plans* (never actuals).
11. **PostgreSQL is the system of record.** FIWARE (optional) is a live-context mirror, reconstructible from Postgres + the event stream.
12. **Status never relies on colour alone.** Text label + icon + badge + pattern/animation, and respect `prefers-reduced-motion`.
13. **Synthetic is labelled synthetic.** Every row carries `data_source` (`SYNTHETIC` | `LIVE` | `MANUAL`). Do not claim real factory data.
14. **3D shows state, not process.** No assembly animations. Allowed motion: camera transitions, progress rings, status pulses, flow-direction chevrons between departments.
15. **Time:** store UTC; one calendar/shift utility; factory timezone from config (`FACTORY_TZ`).

---

## 5. Target architecture and decisions already made

```
         FRONTEND  (Next.js + React + TypeScript + @react-three/fiber)
                          │  REST + WebSocket
                       FastAPI
        ┌─────────────────┼───────────────────┐
   PostgreSQL         ML services          Engines (pure Python)
 (system of record)  LightGBM / HW      capacity · load · root_cause
        │            (MLflow optional)   scheduling (CP-SAT) · simulation (SimPy)
        └── Manufacturing State: Departments → Workstations → Workers → Orders
                          → Loom Units → Component Units → Events
        (optional profile) FIWARE Orion + MongoDB — live-context mirror only
```

**Decisions (do not re-ask):**

| Topic | Decision |
|---|---|
| Frontend | Next.js (App Router), React, **strict TypeScript**, **`@react-three/fiber` + `@react-three/drei`**, Zustand (UI/twin state), TanStack Query (server state), Recharts (2D charts), Tailwind |
| 3D assets | **Procedural primitives** from a registry keyed by `visual_key`; optional GLB later. No per-component hand-placed meshes |
| API | FastAPI, Pydantic v2, Uvicorn, WebSocket; OpenAPI → generated TS types |
| DB | PostgreSQL + SQLAlchemy 2.x + Alembic; surrogate PKs + unique business codes |
| Processing-time ML | LightGBM **quantile** (0.5 / 0.75 / 0.9) |
| Workload forecast | Holt-Winters (`statsmodels`), trend-only fallback when history is short |
| Scheduler | OR-Tools **CP-SAT** |
| Simulation | **SimPy**; one engine shared by synthetic-data generation, live replay, and what-if |
| MLOps | Monitoring + drift in-app first; MLflow registry in a later phase (optional container) |
| FIWARE | Optional compose profile; **off by default** |
| Jobs | CPU-bound work (CP-SAT, SimPy, training) in a process pool, returns `job_id`, polled |
| Tests | pytest, Vitest, Playwright |

---

## 6. Repository structure (target)

```
loom-factory-twin/
├── CLAUDE.md                       # this file
├── docs/                           # detail docs (§8)
├── configs/
│   ├── catalog.yaml                # departments, components, prerequisites, skills, workstation types
│   ├── factory.yaml                # headcount, workstations, shifts, calendar, thresholds, weights
│   └── synthetic/base.yaml
├── docker-compose.yml              # postgres, api, web, (profiles: mlflow, fiware)
├── Makefile
├── legacy/handloom/                # archived original project
├── backend/
│   ├── app/
│   │   ├── api/                    # routers: departments, components, looms, orders, workforce,
│   │   │                           #   capacity, forecast, balancing, what_if, simulation, models, alerts, ingest, ws
│   │   ├── core/                   # config, logging, security, constants, time/shift utility
│   │   ├── db/                     # session, base, seed loaders
│   │   ├── models/                 # SQLAlchemy ORM
│   │   ├── schemas/                # Pydantic I/O
│   │   ├── services/               # orchestration
│   │   ├── tracking/               # state machine, event projection, kit readiness, loom progress
│   │   ├── workforce/              # roster, absence, skill matching
│   │   ├── capacity/               # capacity engine, load classification, bottlenecks
│   │   ├── root_cause/
│   │   ├── balancing/              # recommendation generator + validate_assignment()
│   │   ├── scheduling/             # CP-SAT model + independent feasibility checker
│   │   ├── simulation/             # SimPy engine, event injection, live replay driver
│   │   ├── what_if/
│   │   ├── ml/{build_time,workload_forecast,monitoring,retraining}/
│   │   └── synthetic/              # generator + scenarios A–G + validation
│   ├── tests/
│   └── alembic/
├── frontend/
│   ├── src/app/                    # routes (docs/04)
│   ├── src/twin/                   # R3F scene, pods, component tiles, visual registry
│   ├── src/state/                  # zustand stores + event bus (ported from sandbox/core/EventBus.js)
│   ├── src/api/                    # typed client + single WS provider
│   └── src/components/
└── mlflow/ , fiware/               # optional
```

---

## 7. Legacy reuse (keep / adapt / remove)

| Legacy | Decision | New use |
|---|---|---|
| Three.js scene setup, camera controls, lighting, post-processing | **ADAPT** | Factory floor scene (port to R3F) |
| `EventBus.js` | **KEEP** (port to TS) | Decouples 3D scene from React state |
| `SandboxIsolation.js` concept | **KEEP concept** | Simulation/what-if never touches live |
| `SimulationLoop.js` | **ADAPT** | Playback of SimPy state |
| Alert system + email notifications | **ADAPT** | Manufacturing alert categories (docs/05) |
| Fault injection | **ADAPT** | Event injection (worker absence, material shortage, breakdown…) |
| Demo-mode fallback | **KEEP concept** | Synthetic live-replay driver |
| Dark industrial control-room UI, canvas charts | **KEEP** | Same aesthetic + light/dark toggle |
| Flask relay, `OrionClient.js`, `FlaskRelay.js` | **REPLACE** | FastAPI + WS |
| FIWARE / Mongo | **DEMOTE** | Optional mirror |
| Loom telemetry JSON (`speed, humidity, vibration, thread_break…`) | **REFERENCE ONLY** | Not used by the manufacturing twin. Later: link a finished `LoomUnit` to its operating-loom `device_id` |
| Thread physics, shuttle, weave patterns, RF quality/defect models | **ARCHIVE** | `legacy/` |

**Rule:** first commit only moves old code to `legacy/handloom/`. Build the new system alongside. Delete legacy only after parity.

Known legacy issues **not** to copy: frontend and API both on port 8000; `pip install smtplib` (stdlib); CDN-pinned Three.js r128 without bundler; split sources of truth.

---

## 8. Doc map — read the one for your task

| Working on… | Read |
|---|---|
| Departments, components, DAG, skills, workstations, shifts, state machines, catalog.yaml | `docs/01-domain-departments-components.md` |
| Tables, columns, enums, projections, invariants | `docs/02-data-model.md` |
| Capacity, load, root cause, load balancing, optimizer, prediction, monitoring | `docs/03-capacity-load-balancing-prediction.md` |
| 3D scene, department click-through, panels, routes, accessibility | `docs/04-frontend-3d-twin.md` |
| REST/WS contracts, ingestion, jobs, roles, alerts | `docs/05-api-realtime.md` |
| Synthetic data generator, SimPy engine, scenarios, validation | `docs/06-synthetic-data-simulation.md` |
| Build order, exit criteria, testing, definition of done | `docs/07-build-phases-and-testing.md` |

---

## 9. Build order (summary — details in docs/07)

Do **not** build everything at once. Finish and verify each phase (tests pass, runnable demo) before the next. When told to "continue", resume at the earliest incomplete phase.

```
0 Repo prep → 1 Foundation (DB+catalog+API) → 2 Workforce & shifts → 3 Orders & tracking
→ 4 Synthetic data + SimPy → 5 Capacity/load/root-cause (+ baseline predictions)
→ 6 3D twin UI → 7 ML prediction → 8 Load balancing + CP-SAT + what-if
→ 9 Monitoring/alerts/terminal → 10 Integration (answer all §3 questions end to end)
```

> **Do not build the 3D scene before the data model, state machine and capacity engine exist.** The twin is a view on them. (A frontend shell may start after Phase 3 against seeded data.)

---

## 10. Dev environment

| Service | Port |
|---|---|
| Frontend (Next.js) | 3000 |
| FastAPI | 8000 |
| PostgreSQL | 5432 |
| MLflow (optional) | 5000 |
| FIWARE Orion / MongoDB (optional) | 1026 / 27017 |

```
make up        # docker compose up -d (postgres)  [+ --profile mlflow|fiware]
make migrate   # alembic upgrade head
make seed      # load catalog.yaml + factory.yaml master data
make synth     # python -m app.synthetic.generate --scenario A --months 6 --seed 42 && load
make api       # uvicorn app.main:app --reload --port 8000
make web       # cd frontend && npm run dev
make test      # pytest backend/tests && frontend unit + playwright
make lint      # ruff + mypy + eslint + tsc --noEmit
```

Config via env vars (`.env.example` committed; `.env` git-ignored). Never commit secrets (SMTP credentials for alert email go in env).

---

## 11. Engineering standards

- **Python 3.11+**, type hints everywhere, `ruff` + `mypy`, Pydantic v2. Routers thin → services orchestrate → domain modules (`capacity`, `balancing`, `tracking`, …) are **pure and unit-testable without HTTP/DB**.
- **TypeScript strict**, no `any` without a justifying comment. Types generated from OpenAPI.
- **Config over constants:** thresholds, shift rules, solver limits, objective weights, rule weights.
- **One** calendar/shift utility. Never re-implement shift math.
- **Structured logs**: always log scenario/session id, model version, solver status.
- **Commits:** small, one concern each; no refactor+feature mixing.

### Definition of done (any task)

1. Obeys §4 rules.
2. Tests added/updated and passing; lint/type checks clean.
3. No hard-coded catalog, thresholds, shift numbers, or routes.
4. Explainable outputs carry Problem/Cause/Evidence/Confidence/Action/Impact.
5. Docs updated; Alembic migration included if schema changed.
6. UI changes: keyboard reachable, status not colour-only, reduced-motion respected.

---

## 12. Things not to do

- Don't assign work on free capacity alone — always check skill + workstation eligibility.
- Don't sum capacity across departments or average load across them.
- Don't sum quantiles to aggregate; use Monte Carlo.
- Don't report single-point build times, workloads, or completion dates.
- Don't animate the *building* of components or looms.
- Don't let what-if / simulation / recommendations write to live tables.
- Don't random-split time series; don't leak future data into features.
- Don't feed scenario labels or latent traits into model features.
- Don't generate independent random synthetic values per column.
- Don't hard-code the five departments' components in code (they are catalog data).
- Don't port legacy thread/weave/shuttle code "just in case".
- Don't make FIWARE a source of truth.
- Don't use colour as the only status indicator.

---

## 13. Assumptions made (confirm with the user; all are config, not code)

The user gave one-line department descriptions. The following were **assumed** and must be easy to change:

1. **Component lists per department** (see docs/01) — editable in `catalog.yaml`.
2. **Boundary choices:** motor *driver* sits in Mechatronics (pairs with the motor); *energy meter and optimization controller* sit in Power; the *sensor hub/MCU board* sits in Sensors; the *frame* is built in Assembly.
3. **Shifts:** 2 shifts × 8 h (06:00–14:00, 14:00–22:00) with 0.5 h break → **7.5 productive h**; Mon–Fri; configurable.
4. **Headcount & workstations:** MECH 8, FAB 12, SENS 6, PWR 7, ASSY 18 workers (illustrative; docs/06 sizing).
5. **Loom models:** start with 3 variants (`LM-100` base, `LM-200` with extra tension sensing, `LM-300` high-power) differing by complexity multipliers and component quantities.
6. **Roles:** `planner`, `supervisor`, `dept_lead`, `viewer`.
7. **Real data:** none yet — synthetic + manual event entry; ingestion adapter interface is defined now, implemented later (ERP/MES/barcode/RFID).
8. **Factory timezone:** `FACTORY_TZ` env var (default `UTC`).

**Ask the user before assuming** anything beyond these (real component lists, real headcount, real shift pattern, auth provider, deployment target, MES/ERP integration).
