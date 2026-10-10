# 06 — Synthetic Data Generator & SimPy Simulation

> No real factory data exists yet. All data is **synthetic**, labelled `data_source = "SYNTHETIC"`, produced by a **deterministic, seeded, config-driven** generator that runs on the **same SimPy engine** used by the live twin and what-if. One engine ⇒ history, live replay and what-if share behaviour. Do **not** write a second simulator for data generation.

Legacy loom telemetry (speed, humidity, vibration, thread break…) is **not used** here: it describes a running loom, not a factory building looms. It is reference-only for record style (ISO-8601 UTC, nested groups).

---

## 1. Core principle: generate causes, then derive effects

Never sample each column independently. Generate in dependency order; every downstream value is a **function** of upstream values plus bounded noise.

```
Config/seed
 → L1 Master data        (departments, workstations, workers, skills, catalog, shifts, calendar, materials)
 → L2 Latent traits      (worker skill truth & learning rate, workstation speed/MTBF, component complexity)
 → L3 Demand & orders    (arrivals, mix, quantity, priority, due dates)
 → L4 Ground-truth time  (per component unit processing time with real structure)
 → L5 Execution (SimPy)  (queues, shifts, absences, breakdowns, shortages, QC/rework → events, actual start/end)
 → L6 Projections        (component_unit state, loom_unit state, worker/workstation timelines)
 → L7 Aggregates/labels  (capacity & load snapshots via the REAL capacity engine, forecast targets)
 → L8 Scenario overlays  (A–G)
```

---

## 2. L1 — Master data (defaults; all configurable in `configs/synthetic/base.yaml`)

| Item | Default |
|---|---|
| Departments | 5 (fixed) |
| Component types | 31 (catalog) → 32 units per LM-100 loom (`SENS-LOAD` ×2) |
| Loom models | `LM-100` (1.0×), `LM-200` (+ extra tension sensing; SENS 1.15×, PWR 1.05×), `LM-300` (high power; MECH 1.2×, PWR 1.3×) |
| Workers | 51 (MECH 8, FAB 12, SENS 6, PWR 7, ASSY 18); each holds 1–4 skills, level 1–5; ~15–25% hold a cross-dept skill |
| Workstations | per `docs/01` §4.2 (≈ 35 total); **not dense**; a few single-eligible types |
| Shifts | 2 × (8 h − 0.5 h break), Mon–Fri; holidays 12–15/yr; 1–2 shutdown weeks |
| Materials | 15–30; `BOM` 1–3 lines per component; scrap 1–8% |

### 2.1 Sizing sanity check (illustrative — **verify with the capacity engine in a test**)

Productive 7.5 h/shift, 1 shift per worker/day, efficiency 0.85:

| Dept | Workers | Usable h/day | Std h per LM-100 | Looms/day capacity |
|---|---|---|---|---|
| MECH | 8 | 51.0 | 8.3 | 6.1 |
| FAB | 12 | 76.5 | 12.2 | 6.3 |
| SENS | 6 | 38.3 | 6.4 | 6.0 |
| PWR | 7 | 44.6 | 6.5 | 6.9 |
| ASSY | 18 | 114.8 | 19.5 | **5.9 ← system bottleneck** |

Baseline demand ≈ **5 looms/day** ≈ 85% of the bottleneck ⇒ scenario A is mostly HEALTHY (70–95%). Skill-pool and workstation limits will bind earlier than these raw numbers; that is expected and *desired* (creates realistic bottlenecks).

---

## 3. L2 — Latent traits (hidden "truth"; stored in `gt_latent_traits`; never a feature)

| Trait | Distribution | Effect |
|---|---|---|
| `worker.skill_true[skill]` | level (1–5) + small continuous offset | scales build time and reject rate |
| `worker.learning_rate` | Beta around 0.05–0.15 | time falls with repetitions of the same component (power-law), floors at a skill-dependent asymptote |
| `worker.reliability` | Beta | absence propensity |
| `workstation.speed_factor` | lognormal(0, 0.10), clip 0.8–1.25 | scales time |
| `workstation.mtbf / mttr` | Weibull / lognormal (hours) | breakdown frequency & duration (benches with tools: low rate; test rigs: moderate) |
| `component.complexity` | lognormal around 1.0, per loom model multiplier | scales std setup/run time |
| `dept.team_efficiency` | slow random walk around 0.85 | shared factor → correlated errors within a dept |

---

## 4. L3 — Demand & orders

```
λ_day = base_rate × (1 + trend·t) × seasonality(dow, month) × scenario_multiplier
N_orders ~ NegativeBinomial(mean = λ_day / mean_order_size, dispersion = k)     # over-dispersed
```
- **Order size:** lognormal, min 1 (typical 2–12 looms).
- **Model mix:** Dirichlet over {LM-100, LM-200, LM-300}, slowly drifting; seasonal tilt for one model.
- **Priority:** categorical 70% NORMAL / 20% HIGH / 8% URGENT / 2% CRITICAL; urgent orders get short due dates.
- **Due date:** `release + Σ(critical-path std hours) × queue_factor + slack`, `queue_factor ∈ [1.5, 4]`, slack lognormal — due-date pressure *emerges* when demand rises; it is not hard-coded.
- **Release:** most release on arrival; some late (material arrival) ⇒ natural late-starts.

---

## 5. L4 — Ground-truth build time (the target the ML model must learn)

```
setup_h  = std_setup(component) × changeover(prev_component_type → this) × (1 + ε_s)
cycle_h  = std_h(component) × complexity(component, loom_model)
           × workstation.speed_factor
           × skill_multiplier(worker.skill_true)          # 1.00 → 0.80 as level 1→5
           × learning_multiplier(worker, reps_of_component) # power-law, floors
           × batch_multiplier(batch_position)             # mild fatigue / warm-up
           × fatigue_multiplier(hour_of_shift)            # last 90 min slightly slower
           × team_efficiency_inverse(dept, t)             # shared dept factor
           × (1 + drift(t))                               # 0 normally; ramps in scenario G
           × exp(ε_c),  ε_c ~ N(0, σ(component, worker, workstation))    # heteroscedastic
crew_adjust = crew_size scaling (sub-linear: 2 workers ≈ 1.7× speed)
processing_h = setup_h + cycle_h / crew_adjust + disruptions   # disruptions: tool issue, re-clamp, re-measure, wait-for-QC
```

Requirements:
- **Right-skewed:** lognormal noise + occasional disruption add-ons so **P90/P50 ≈ 1.15–2.0** for most (component, workstation, skill) groups. If P50 ≈ P90 the quantile model has nothing to learn.
- **Heteroscedastic:** noise widens for complex components, junior workers (level ≤ 2), worn tools, first units after changeover.
- `std_h` stays the **planned** value; actual differs systematically — that gap is what the model learns.
- **Quality:** `P(QC fail) = 1 − first_pass_yield_adj`, where yield falls with low skill, complexity, fatigue, scenario effects. Fail ⇒ `REWORK` (extra hours, 20–60% of std) or `REJECT` (≈ 10% of fails) ⇒ replacement unit.

---

## 6. L5 — Execution (SimPy), shared with `simulation/`

Process per component unit: `RELEASE → (wait prereqs) → READY → QUEUE → needs [eligible workstation + qualified worker(s) + material + shift hours] → START → work → QC → COMPLETE | REWORK | REJECT`.

**Dispatch rule** (configurable): mix of earliest-due-date, priority, shortest-queue-for-eligible-workstation, and "keep critical path moving"; tie-break deterministically.

**Disruptions are sampled, not scripted:**
- **Workstation breakdown:** per-workstation Weibull from MTBF; duration from MTTR; WIP accumulates upstream; unit in progress → `BLOCKED(WORKSTATION_DOWN)`.
- **Absences:** per worker per day ≈ Bernoulli(3–6% modulated by reliability) + planned leave; absent ⇒ roster hole; skill-pool shrinks ⇒ `BLOCKED(WORKER_UNAVAILABLE|SKILL_GAP)`.
- **Material shortage:** inventory depletes via `MaterialTransaction`s, replenishes with lead time (+ variability); shortage ⇒ `BLOCKED(MATERIAL)`.
- **Maintenance:** planned windows per workstation (+ reactive after breakdown).
- **Shifts/breaks:** workers only work within shift windows; no work during breaks; handover state carried across shifts.
- **Loans:** an optional policy lets the simulator lend cross-skilled workers (used in what-if and by applied recommendations).

Time advance: event-driven (SimPy), **not** fixed-step; the live driver replays at `speedup×` and emits WS events.

**L5 outputs:** `loom_build_order`, `loom_unit`, `component_unit` (planned vs actual), `component_event` stream, `workstation_event`, `worker_availability`, `attendance_log`, `material_transaction`, `inventory` snapshots.

**History and "now":** the final day of the run is the *current* production state (open orders, queued units, units mid-build, today's roster) so the live twin is populated on first launch.

---

## 7. L7 — Aggregates and labels (via the real engines)

Computed by calling `capacity/` and `ml/` **modules** — never hand-written:
- Per dept / workstation / shift / day / week: capacity layers, workload, load %, WIP, queue length, utilisation.
- Load class labels from configurable thresholds (UNDERLOAD / HEALTHY / OVERLOAD / OVERLOAD_RISK).
- Forecast targets: daily released looms; daily dept workload hours.
- Planned-vs-actual joins for monitoring/drift.

Training data and live system therefore **cannot disagree** on definitions.

---

## 8. L8 — Scenarios A–G (parameter overlays; combinable, e.g. B + F)

| ID | Scenario | Parameter changes | Signature asserted in tests |
|---|---|---|---|
| **A** | Healthy | demand ≈ 80–90% of bottleneck capacity; nominal MTBF/absence; materials OK | most depts 70–95%; low late rate; coverage ≈ 75/90 |
| **B** | Overload / demand surge | demand ×1.3–1.6 for 3–6 weeks; more urgent orders; tighter due dates | bottleneck dept > 95% load; WIP ↑ ≥ 30%; late looms rise; `ASY-*` starved/queued appropriately |
| **C** | Underload | demand ×0.4–0.6; same staff | many depts < 70%; root cause `LOW_DEMAND` |
| **D** | Workstation breakdown | critical single-eligible bench (`HV_TEST_BENCH` or `CALIB_STATION`) down 4–72 h | WIP builds before it, starvation after; **no ineligible alternate used** |
| **E** | Material shortage | delay/cut a material (e.g. load cells / HX711) used by several components | `BLOCKED(MATERIAL)`; SENS idle despite staff; downstream `ASY-SENSOR` starved |
| **F** | Worker / skill shortage | absences concentrated on workers with a specific skill (e.g. `SK-SOLDER≥3`) | machines free but `BLOCKED(SKILL_GAP)`; underload cause `SKILL_SHORTAGE`; cross-skill lend recommendations considered |
| **G** | Build-time drift | `drift(t)` ramps 0 → +12–20% over 6–10 weeks on chosen components/workers (e.g. new-hire cohort or tool wear) | error ↑, P75/P90 coverage ↓, PSI/KS flags, **retraining recommendation fires** |

Each scenario stores `scenario_id`, `injected_cause`, scope, start/end in `gt_scenario_label` (evaluation only — e.g. "did root-cause find `SKILL_SHORTAGE` in F?"). **Never a model feature.**

---

## 9. Outputs and CLI

```
data/synthetic/<run_id>/
  master/         departments, workstations, workers, worker_skills, skills, components, prerequisites,
                  loom_models, shifts, calendar, materials, bom     (Parquet + CSV)
  transactional/  orders, loom_units, component_units, component_events, workstation_events,
                  worker_availability, attendance, material_transactions, inventory_snapshots
  aggregates/     capacity_snapshots, load_snapshots, daily_dept_metrics, forecast_targets
  ground_truth/   latent_traits, scenario_labels
  sample/         sample_events.json       (small slice for demo/streamer)
  manifest.json   (seed, config hash, scenarios, row counts, generator version)
```

```
python -m app.synthetic.generate --config configs/synthetic/base.yaml --scenario A --months 6 --seed 42
python -m app.synthetic.generate --scenario F --months 6 --seed 42
python -m app.synthetic.generate --scenario G --months 8 --seed 42 --drift-start 2026-03-01
python -m app.synthetic.load     --run <run_id>          # COPY in FK order: master → transactional → aggregates
python -m app.synthetic.validate --run <run_id>
```

- Same `(config, scenario, seed, generator_version)` ⇒ **byte-identical** output.
- Default history: **6 months** (≈ 120 working days, ~600 looms, ~19k component units, ~150–250k events). Longer (12–18 months) is optional for seasonality.
- Streamer (**live driver**): replays `component_event`s into the API/WS at configurable speedup so the twin is "live" in demo mode (successor of the handloom `stream_fi.py`/demo-mode idea).

---

## 10. Validation (`synthetic.validate`) — must pass before data is accepted

**Structural**
- Every component type has an eligible workstation + qualified worker; every unit's actual workstation/worker was eligible/qualified.
- Prerequisites respected: no unit starts before its prerequisite units are `COMPLETED` (+ transfer time).
- Event streams are legal walks of the state machine; `rebuild_projection()` equals stored projection.
- No worker on two units at once; no worker beyond max hours/day; no workstation double-booked.
- Material balances reconcile (no negative inventory).
- No NaNs; all rates in range.

**Statistical (the "not independent random" checks)**
- `corr(actual_h/std_h, worker_skill) < 0`; `corr(actual_h/std_h, complexity) > 0`; `corr(rework_prob, skill) < 0`.
- Learning curve visible: mean time of a worker's n-th unit of a component < first unit.
- P90/P50 ratio within ~1.15–2.0 for the majority of groups.
- Breakdown/absence rates match configured parameters (within CI).
- `corr(dept_load, queue_length) > 0`; downstream starvation follows upstream outage.
- Demand shows trend + seasonality (STL/ACF check).
- Load distribution: A mostly HEALTHY; B/C as specified.

**Scenario:** each scenario's signature (§8) asserted in integration tests; G triggers monitoring + retrain recommendation.

---

## 11. Anti-patterns

- ❌ `np.random.uniform` per column for times, loads, utilisation
- ❌ Dense "every worker can do everything / every bench fits every component"
- ❌ A universal timing shared by all components, workers or looms
- ❌ Hand-written load % or labels instead of computing from capacity + workload
- ❌ Unseeded RNG / wall-clock dependence
- ❌ Feeding `gt_*` or scenario labels into ML features
- ❌ Events that don't reconcile with unit state and worker/workstation timelines
- ❌ A second simulator for data generation
- ❌ Reusing loom-operation telemetry values for the manufacturing twin

---

## 12. Simulation controls & event injection (`simulation/`)

- **Controls:** `START, PAUSE, RESET, +1 HOUR, +1 SHIFT, +1 DAY` (+ speed). Sandbox sessions operate on a **snapshot** (`sim_session`), never live tables.
- **Injection (replaces handloom fault injection):** `WORKER_ABSENCE`, `MATERIAL_SHORTAGE`, `WORKSTATION_BREAKDOWN`, `DEMAND_SPIKE`, `DEMAND_DROP`, `URGENT_ORDER`, `TIME_INFLATION`, `REWORK_SURGE`, `PRODUCT_MIX_CHANGE`, `LOAN_WORKER`, `RESTORE_NORMAL`.
- Sample durations from the model distributions (Expected/P75/P90 → lognormal) instead of fixed values.
- **Reproducible:** `(snapshot, seed, events)` ⇒ identical output (tested).
- Push state to the frontend over WS as **events**, not full-state polls.
