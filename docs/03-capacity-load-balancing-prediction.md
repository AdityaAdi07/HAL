# 03 — Capacity, Load, Root Cause, Load Balancing, Prediction

> Pure, unit-testable Python modules under `capacity/`, `root_cause/`, `balancing/`, `scheduling/`, `ml/`. Routers only call services. All numbers below that look like defaults come from config.

---

## 1. Capacity engine — `capacity/`

Unit: **hours** (worker-hours of productive time). Computed per **Workstation → Department** and per **skill pool → Department**, for windows `SHIFT | DAY | WEEK`.

```
Theoretical_h = Σ workstations × shift_length_h × shifts_in_window
Scheduled_h   = Theoretical_h − holidays/shutdowns (calendar)
Available_ws_h= Scheduled_h − planned maintenance − breaks − known workstation downtime
Labour_h      = Σ present workers (roster − absences) × productive_h × (qualified for dept's open work)
Binding_h     = min(Available_ws_h, Labour_h)     # evaluated per skill pool, then summed (a pool can bind)
Usable_h      = Binding_h × Efficiency × Material_factor
```

- `Efficiency` = rolling (standard hours *earned* ÷ actual hours worked) for that dept; clamp `[0.3, 1.2]`; fall back to config default (0.85) when < N completed units.
- `Material_factor` = hours-weighted share of the window's workload whose materials are on hand.
- **Skill pools:** if all open work needs `SK-SOLDER≥3` and only 2 such workers are present, Labour_h counts those 2, not the whole department.
- **Capacity reported with a pessimistic bound:** `Usable_h` (expected) and `Usable_h_p10` (pessimistic: higher absence, lower efficiency). Used for *stress load* (§2).
- **Zero guard:** `Usable_h == 0` ⇒ load class `UNAVAILABLE`, load = `null` (never NaN/crash).
- **Throughput capacity (looms/day)** per dept = `Usable_h(day) ÷ std_h_per_loom(dept, order mix)`. **System throughput = min over depts.** *Do not sum or average department capacity.*

Levels: Workstation, Worker (individual availability), Department. No "factory capacity hours" number exists — only per-dept loads and the system throughput.

### 1.1 Current vs predicted capacity (what the UI shows)

| View | Definition |
|---|---|
| **Current shift** | Window = the running shift: rostered/present workers now, workstation up/down now |
| **Today** | Both shifts (completed + remaining) |
| **This week** | Mon–Fri with known leave/shutdowns |
| **Predicted** (7 / 30 / 90 d) | Roster plan + calendar + planned maintenance + modelled absence rate + efficiency trend → `{expected, pessimistic}` per day/week |

---

## 2. Workload and load

### 2.1 Workload (hours demanded in a window)

```
Workload = Σ over open ComponentUnits scheduled/expected in window of
             remaining_expected_h = expected_h × (1 − progress) + expected_rework_h
         + Σ forecast not-yet-released orders × catalog hours   (beyond released horizon)
```
`expected_rework_h = (1 − first_pass_yield) × rework_hours_per_failure`.

### 2.2 Distribution — never sum quantiles

Each open unit has a predicted distribution (from `(P50, P75, P90)` fit a lognormal; see §6.1). **Aggregate with Monte Carlo** (default 2,000 draws, seeded) including a configurable shared-factor (e.g. department-wide efficiency draw, correlation ρ) so aggregate variance isn't understated. Report **Expected (mean of draws), P75, P90** of department workload. Test: `P90(aggregate) < Σ P90(units)` for ≥ 2 units.

### 2.3 Load

```
Load_expected = Workload_expected / Usable_h × 100
Load_p75      = Workload_p75      / Usable_h × 100
Load_p90      = Workload_p90      / Usable_h × 100
Stress_load   = Workload_p90      / Usable_h_p10 × 100          # worst plausible
Capacity_balance_h = Workload_expected − Usable_h               # +ve = shortfall
```

### 2.4 Classification (ordered rules; return `rule_fired`)

```
R0 UNAVAILABLE   : Usable_h == 0
R1 OVERLOAD      : Load_expected  >  over_threshold            (default 95)
R2 OVERLOAD_RISK : Load_expected <= over_threshold AND Load_{risk_quantile} > over_threshold   (default risk_quantile = p75)
R3 UNDERLOAD     : Load_expected  <  under_threshold           (default 70)
R4 HEALTHY       : otherwise     (70 ≤ Load_expected ≤ 95)
```
Boundary tests: **69.9 → UNDERLOAD, 70 → HEALTHY, 95 → HEALTHY, 95.1 → OVERLOAD.**
Orthogonal flags: `STARVED` (idle due to unmet prerequisites / WIP cap), `SHORT_STAFFED` (Labour_h < Available_ws_h), `MATERIAL_CONSTRAINED`, `SKILL_BOUND`.

### 2.5 Bottleneck detection (rule-based, weights in config)

Signals: high load, long ready-queue, long wait time, high WIP, build-time inflation vs standard, assembly starved by this dept, single-eligible-workstation components, skill-pool binding.
Output: `{bottleneck_dept, bottleneck_component_types[], bottleneck_workstation_type, reason, evidence}`. Also compute the **system bottleneck** = dept with minimum looms/day throughput (and the next one — "second bottleneck").

---

## 3. Root-cause engine — `root_cause/`

Every output: **`Problem | Cause | Evidence | Confidence | Recommended Action | Expected Impact`** (JSON schema in §3.3). Evidence is pulled from DB/engines; no templated prose with invented numbers.

### 3.1 Cause taxonomy

- **Underload causes:** `LOW_DEMAND`, `MATERIAL_SHORTAGE`, `WORKER_ABSENCE`, `SKILL_SHORTAGE`, `WORKSTATION_DOWN`, `UPSTREAM_STARVATION` (waiting on prerequisites), `RELEASE_PACING` (WIP cap / release limited by system bottleneck), `SCHEDULING_IMBALANCE`, `WORK_ASSIGNED_ELSEWHERE`
- **Overload causes:** `DEPT_BOTTLENECK`, `WORKER_SHORTAGE`, `SKILL_SHORTAGE`, `URGENT_ORDER`, `DUE_DATE_PRESSURE`, `WIP_ACCUMULATION`, `REWORK_SURGE`, `TIME_INFLATION`, `DEMAND_SPIKE`, `WORKSTATION_DOWN`, `SHIFT_GAP`
- **Other problem types:** `LATE_ORDER` (which loom, which component is on the critical path), `CAPACITY_SHORTAGE` (capacity_balance > 0 over horizon)

### 3.2 Decision order (underload example)

1. Demand low? (released + forecast workload below capacity, other depts normal) → `LOW_DEMAND`
2. Material blocking units? → `MATERIAL_SHORTAGE`
3. Present qualified workers < required? → `WORKER_ABSENCE` / `SKILL_SHORTAGE`
4. Workstations down? → `WORKSTATION_DOWN`
5. Idle with READY queue empty because prereqs/WIP cap? → `UPSTREAM_STARVATION` / `RELEASE_PACING`
6. READY work exists but sits with another worker/workstation that is eligible here → `SCHEDULING_IMBALANCE` / `WORK_ASSIGNED_ELSEWHERE`

### 3.3 Output schema

```json
{
  "problem": "DEPT-SENS expected load 46% (UNDERLOAD)",
  "cause": "RELEASE_PACING",
  "evidence": {
    "load": {"expected": 46.1, "p75": 55.3, "p90": 61.0},
    "queue_ready_units": 3,
    "system_bottleneck": {"dept": "DEPT-ASSY", "looms_per_day": 5.4},
    "wip_cap": {"limit_looms_ahead": 2, "current": 2}
  },
  "confidence": 0.82,
  "recommended_action": {"type": "LEND_WORKER", "from": "DEPT-SENS", "to": "DEPT-PWR", "n": 2, "shift": "SHIFT-A", "days": 3},
  "expected_impact": {"DEPT-PWR.load_p75": {"before": 104.2, "after": 91.0}}
}
```

---

## 4. Load balancing — `balancing/`

### 4.1 Three levels

| Level | Question | Levers |
|---|---|---|
| **L1 Intra-department** | Are tasks spread across eligible workstations/workers? | `REASSIGN_TASK`, `SPLIT_CREW` (crew_size↑), `RESEQUENCE` |
| **L2 Inter-department** | Is one department drowning while another idles? | `LEND_WORKER` (via skill overlap only), `ADD_SHIFT`/`OVERTIME`, `RESCHEDULE_MAINTENANCE` |
| **L3 Flow / release** | Are we feeding the system faster than the bottleneck can drain it? | `PACE_RELEASE` (drum-buffer-rope: release looms at the bottleneck rate), `SET_WIP_CAP`, `EXPEDITE_MATERIAL` (flag only) |

### 4.2 Recommendation generation (rule-first, optimizer-backed)

1. From `load_snapshot` + root cause, pick candidate levers for each OVERLOAD / OVERLOAD_RISK / UNDERLOAD department.
2. Build concrete candidate actions (e.g. *move unit X to workstation Y, worker W*).
3. **`validate_assignment()` — every candidate runs all checks; any failure ⇒ discard (record in `checks_json`):**
   - **V1 Skill:** worker level ≥ component min level, certification valid
   - **V2 Workstation:** eligible type, workstation up, free in the slot
   - **V3 Hours/shift:** within `max_scheduled_h/day`, ≤ 1 shift/day, break rules, overtime cap
   - **V4 Material:** requirements available by start
   - **V5 Prerequisites:** all prereq units `COMPLETED` by start (or scheduled to be)
   - **V6 Capacity:** target resource's resulting load ≤ `over_threshold` (or strictly better than before)
   - **V7 Crew:** crew_size satisfied simultaneously
   - **V8 No-conflict:** worker/workstation not double-booked; loan doesn't strand the home dept below its own required skill coverage
4. **Simulate** survivors in SimPy on a snapshot → `before/after/delta` (late looms, dept loads, WIP, completion P90). Keep only actions that improve the objective.
5. Persist `recommendation` with Problem/Cause/Evidence/Confidence/Action/Impact + `checks_json` + `sim_before_after_json`.
6. **Apply** (explicit, audited, role-gated) writes **plan** rows (`schedule_assignment`, roster `LOAN/OVERTIME`) — never actuals.

### 4.3 Worked examples to reproduce in tests

**E1 — Lend a worker (underload ↔ overload).** `DEPT-SENS` expected load 46% (cause `RELEASE_PACING`), `DEPT-PWR` P75 load 104%. Two SENS workers hold `SK-SOLDER≥3` and `SK-ELEC-WIRING≥2` (valid), are on SHIFT-A with no required local work. Recommendation **"Lend 2 SENS workers → PWR, SHIFT-A, 3 days"** is emitted **only** if V1–V8 pass; impact computed by SimPy (e.g. PWR P75 104 → ~91%). If SENS has *only* one qualified worker free, the action must be rejected or reduced to `n=1` and the reason recorded.

**E2 — Overload risk.** `DEPT-FAB` expected 88% (HEALTHY) but P75 97% → `OVERLOAD_RISK`, cause `TIME_INFLATION` on `FAB-HEDDLE`. Candidate actions: `OVERTIME(2h, 3 workers)`, `LEND_WORKER` from MECH via `SK-MECH`, `PACE_RELEASE`. Show each with checks and simulated delta; rank by objective gain.

**E3 — Workstation down.** `HV_TEST_BENCH` down 6 h (single eligible bench for `PWR-OPT`): expect P90 loom completion to slip, `PWR-OPT` queue to grow, `ASY-POWER` starved. The only valid mitigations: `RESEQUENCE`, `EXPEDITE`, `ADD_SHIFT`; **no** "move to another workstation" candidate may be emitted (none eligible) — assert this.

### 4.4 Optimizer — `scheduling/` (OR-Tools CP-SAT)

Goal: a **feasible** plan, not a pretty one.

- **Tasks:** open `ComponentUnit`s in a rolling horizon (default 7 working days), plus crew duplicates.
- **Decision vars:** optional interval per (unit, eligible workstation, qualified worker[s]); exactly one chosen per unit.
- **Hard constraints:** skill & workstation eligibility; precedence DAG (+ transfer time); material availability dates; worker shift windows, max h/day, one task at a time per worker; `NoOverlap` per workstation; calendar/holidays/maintenance; crew size; WIP cap/kit-lead limit.
- **Objective (weights in config):** minimise `late looms + total tardiness + max department load + load imbalance + overtime + loans + WIP + changeovers`.
- **Duration quantile:** plan on **P75** by default (configurable); the plan records which quantile.
- **Time scale:** integer minutes.
- **Output:** best feasible plan + `solver_status` (`OPTIMAL | FEASIBLE | INFEASIBLE | UNKNOWN`) + gap + objective breakdown + **diff vs current plan** ("Changed Assignments").
- **Infeasible ⇒ diagnose:** relax constraint groups one at a time (material, skill, hours, deadlines) and report *which group blocks it*, not a bare error.
- **Independent feasibility checker** (separate code path) re-verifies every hard constraint on solver output; used in tests and before persisting.
- Solver time limit and workers configurable; log status, gap, scenario/session id.

---

## 5. What-if engine — `what_if/`

Scenarios: `WORKER_ABSENCE`, `ADD_SHIFT`, `REMOVE_SHIFT`, `OVERTIME`, `LOAN_WORKER`, `MATERIAL_SHORTAGE`, `MATERIAL_ARRIVAL`, `WORKSTATION_BREAKDOWN`, `DEMAND_SPIKE`, `DEMAND_DROP`, `URGENT_ORDER`, `CHANGE_DUE_DATE`, `CHANGE_PRIORITY`, `TIME_INFLATION(+x%)`, `REWORK_SURGE`, `PACE_RELEASE_CHANGE`.

Flow: scenario → **snapshot** → SimPy run (seeded; sample times from fitted distributions) → optional CP-SAT re-optimise → **BEFORE / AFTER / DELTA** for: dept Expected/P75/P90 load, late looms, WIP, worker utilisation, workstation utilisation, bottleneck, material shortages, loom completion P50/P90 → recommended action (only if V1–V8 pass).

Worked test: `WORKER_ABSENCE` — 3 of 6 SENS workers with `SK-SOLDER≥3` absent for 2 days ⇒ `SKILL_SHORTAGE`, SENS load ↑ >100%, `ASY-SENSOR` starved; recommendation lists valid cross-skill lenders or says none exist.

---

## 6. Prediction — `ml/`

### 6.1 P1: Component build-time model (`ml/build_time/`)

- **LightGBM quantile regression**: three models, alpha = 0.5 / 0.75 / 0.9 → Expected(P50) / P75 / P90 hours.
- **Unit of prediction:** `ComponentType × Workstation × Worker (skill level) × context`.
- **Post-process:** enforce monotone quantiles (P50 ≤ P75 ≤ P90). For aggregation, fit lognormal to the three quantiles.
- **Features:** component_type, dept, workstation (type + id), worker skill level for the required skill, worker experience on this component (count of prior units — learning curve), crew size, loom_model complexity, order quantity / batch position, shift, hour-of-shift, day-of-week, queue length at start, rolling mean/std of last K actual hours for (type, workstation) and (type, worker), std hours, rework history, material-ready flag, product mix, priority.
- **Leakage rules:** rolling features use data **strictly before** prediction time; **time-based splits only** (train → validate → test chronologically); test `test_no_leakage` perturbs future rows and asserts predictions unchanged.
- **Cold start** (new component/worker/workstation): fall back to `std_hours × complexity` with empirical dispersion from similar types; set `fallback_used=true`, low confidence.
- **Baseline predictor (Phase 5, before ML):** same interface; Expected = `std_h × complexity × empirical_ratio(type)`, P75/P90 from empirical quantiles of historical actual/std ratio. ML must **beat the baseline** on holdout to be promoted.
- **Example output:** `FAB-HEDDLE / HEDDLE_REED_JIG / worker L3 → Expected 3.2 h · P75 3.7 h · P90 4.4 h`.

### 6.2 P2: Workload forecast (`ml/workload_forecast/`)

- Holt-Winters (additive/multiplicative trend, weekly seasonality) on **daily released loom orders** and on **department workload hours**.
- Horizons **7, 30, 90 days**. Levels: **Factory (looms/day), Department, Component type (filter)**.
- `P75/P90` from forecast intervals or residual quantiles — **document which** in `forecast.method_note`.
- Short history (< 2 seasonal cycles) ⇒ trend-only, and say so in the response.

### 6.3 P3: Capacity forecast (deterministic + stochastic)

`Capacity_h(day) = roster_plan × productive_h × (1 − absence_rate(dept, dow)) × efficiency_trend − planned maintenance`. Expected + pessimistic (P10) via sampled absences. Absence rate learned from `worker_availability` history.

### 6.4 P4: Loom completion prediction (`simulation/`)

Monte Carlo over the DAG per open loom unit: sample unit times from P1 distributions, apply current queues/capacity/roster, respect priorities. N = 500 replications (seeded). Output: completion `{expected, P75, P90}`, **on-time probability** vs due date, **critical department** (most frequently on the critical path), blocking component. Stored in `prediction_loom`.

### 6.5 Monitoring (`ml/monitoring/`)

Metrics: **MAE, RMSE, WAPE, Bias, Quantile loss, P75 coverage, P90 coverage** — computed **overall, per department, and per load segment (UNDERLOAD/HEALTHY/OVERLOAD)**, never only overall MAE. Healthy: P75 coverage ≈ 75%, P90 ≈ 90%. Drift (PSI/KS/chi-square) on: actual/std ratio, worker mix, workstation mix, component mix, rework rate, queue length; plus missing values and new categories.

### 6.6 Retraining (`ml/retraining/`)

`Monitoring → degradation/drift → recommendation → train challenger → time-split backtest → champion vs challenger → validation → promote/reject → registry (MLflow optional)`.
Compare overall + per-dept + per-load-segment MAE/WAPE, quantile loss, coverage, and **critical department/component** performance. A challenger that wins overall but regresses on **OVERLOAD segment or the system-bottleneck department** must **not** auto-promote. Statuses `CHAMPION, CHALLENGER, PROMOTED, REJECTED, ROLLED_BACK`; rollback = one call.
