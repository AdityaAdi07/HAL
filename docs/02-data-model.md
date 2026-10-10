# 02 — Data Model

> SQLAlchemy 2.x models + Alembic migrations + Pydantic v2 schemas. Surrogate PKs (UUID or bigint) **plus** unique indexed business codes (`DEPT-FAB`, `LM100-000123`, `WO-…`). All timestamps `timestamptz` in UTC. Every transactional/telemetry-like table has `data_source` (`SYNTHETIC|LIVE|MANUAL`).

---

## 1. Master data

| Table | Key columns |
|---|---|
| `department` | `code`, `dept_no`, `name`, `layout_json`, `lead_worker_id`, `threshold_overrides_json` |
| `workstation_type` | `code`, `dept_id`, `name` |
| `workstation` | `code`, `dept_id`, `type_id`, `name`, `status` (`AVAILABLE, IN_USE, DOWN, MAINTENANCE`), `speed_factor_hint` (nullable, **never** the latent truth), `commissioned_on` |
| `skill` | `code`, `name` |
| `component_type` | `code`, `dept_id`, `name`, `std_hours`, `std_setup_hours`, `crew_size`, `required_skill_id`, `min_skill_level`, `first_pass_yield`, `visual_key`, `sequence_hint` |
| `component_type_workstation_type` | `component_type_id`, `workstation_type_id`, `preference_rank` (eligibility; **not dense**) |
| `component_prerequisite` | `component_type_id`, `prerequisite_type_id`, `transfer_time_h` — DAG edges |
| `loom_model` | `code`, `name`, `complexity_multiplier`, `active` |
| `loom_model_component` | `loom_model_id`, `component_type_id`, `qty_per_loom`, `complexity_multiplier` |
| `material` | `code`, `name`, `unit`, `lead_time_days`, `safety_stock` |
| `bom_line` | `component_type_id`, `material_id`, `qty_per_unit`, `scrap_factor` |
| `shift_template` | `code`, `name`, `start_time`, `end_time`, `break_h`, `productive_h` (derived/validated) |
| `calendar_day` | `date`, `is_working`, `kind` (`HOLIDAY, SHUTDOWN, NORMAL`), `note` |
| `config_threshold` | `scope_type` (`GLOBAL, DEPT, WORKSTATION`), `scope_id`, `key`, `value` — load thresholds, risk quantile, etc. |

## 2. Workforce

| Table | Key columns |
|---|---|
| `worker` | `code`, `name`, `home_dept_id`, `employment` (`FULL, TEMP`), `hired_on`, `active` |
| `worker_skill` | `worker_id`, `skill_id`, `level` (1–5), `certified_on`, `valid_to` |
| `roster_assignment` | `worker_id`, `date`, `shift_template_id`, `dept_id` (**may differ from home dept ⇒ a loan**), `kind` (`REGULAR, OVERTIME, LOAN`), `planned_hours` |
| `worker_availability` | `worker_id`, `date`, `status` (`PRESENT, ABSENT, LEAVE, LATE, SICK`), `reported_at` |
| `attendance_log` | `worker_id`, `check_in`, `check_out`, `workstation_id` |

Invariant: a worker has **≤ 1 roster row per date**, and `planned_hours ≤ max_scheduled_hours + max_overtime`.

## 3. Transactional data

| Table | Key columns |
|---|---|
| `loom_build_order` | `code`, `loom_model_id`, `quantity`, `priority` (`NORMAL, HIGH, URGENT, CRITICAL`), `release_at`, `due_at`, `status` (`PLANNED, RELEASED, IN_PROGRESS, COMPLETED, CANCELLED, LATE`), `customer_ref` |
| `loom_unit` | `serial`, `order_id`, `status`, `stage`, `progress_pct`, `released_at`, `planned_complete_at`, `actual_complete_at`, `operating_device_id` (nullable; future link to legacy operating-loom twin) |
| `component_unit` | `loom_unit_id`, `component_type_id`, `ordinal` (for qty>1), `dept_id` (denormalised), `status`, `block_reason`, `progress_pct`, `progress_source`, `workstation_id`, `worker_ids[]` (crew), `planned_start/end`, `actual_start/end`, `expected_h`, `p75_h`, `p90_h`, `worked_h`, `rework_count`, `replaces_id`, `queue_entered_at`, `ready_at` |
| `component_event` | **append-only.** `id`, `ts`, `component_unit_id`, `event_type`, `workstation_id`, `worker_id`, `progress_pct`, `qty_good`, `qty_rejected`, `reason_code`, `payload_json`, `data_source` |
| `inventory` | `material_id`, `available`, `reserved`, `incoming`, `expected_arrival`, `as_of` |
| `material_transaction` | `material_id`, `component_unit_id`, `type` (`ISSUE, RECEIPT, SCRAP, ADJUST`), `qty`, `ts` |
| `workstation_event` | `workstation_id`, `ts`, `type` (`UP, DOWN, MAINTENANCE_START, MAINTENANCE_END`), `reason_code` |

**Event types (`component_event.event_type`):**
`RELEASE, READY, QUEUE, START, PROGRESS, PAUSE, RESUME, BLOCK, UNBLOCK, QC_START, QC_PASS, QC_FAIL, REWORK_START, REJECT, COMPLETE, REOPEN, REASSIGN`

`reason_code` examples: `MATERIAL_SHORTAGE, WORKER_ABSENT, SKILL_GAP, WORKSTATION_DOWN, UPSTREAM_PREREQ, QC_DIMENSIONAL, QC_ELECTRICAL, QC_CALIBRATION, TOOL_ISSUE, OTHER`.

### 3.1 Projection rule

`component_unit.status/progress_pct/worked_h/actual_*` are a **projection** of `component_event`. Implement as a single `apply_event(unit, event)` function in `tracking/` used by: API ingest, live replay, synthetic loader, and tests. The projection is updated **in the same DB transaction** as the event insert. A `rebuild_projection()` command must reproduce identical state from events alone (tested).

## 4. Intelligence outputs (derived, versioned)

| Table | Key columns |
|---|---|
| `capacity_snapshot` | `scope_type` (`WORKSTATION, WORKER_POOL, DEPT`), `scope_id`, `window_type` (`SHIFT, DAY, WEEK`), `window_start`, `theoretical_h`, `scheduled_h`, `available_h`, `labour_h`, `usable_h`, `efficiency`, `material_factor`, `calc_version` |
| `load_snapshot` | `dept_id`, `window_start`, `horizon_days`, `workload_exp_h`, `workload_p75_h`, `workload_p90_h`, `load_exp_pct`, `load_p75_pct`, `load_p90_pct`, `capacity_balance_h`, `load_class`, `rule_fired`, `flags[]` |
| `forecast` | `scope_type`, `scope_id`, `metric` (`WORKLOAD_H`, `ORDERS`, `CAPACITY_H`), `horizon_days`, `ts`, `expected`, `p75`, `p90`, `model_version`, `method_note` |
| `prediction_component` | `component_unit_id`, `made_at`, `expected_h`, `p75_h`, `p90_h`, `model_version`, `confidence`, `fallback_used` |
| `prediction_loom` | `loom_unit_id`, `made_at`, `complete_expected`, `complete_p75`, `complete_p90`, `on_time_prob`, `critical_dept_id`, `n_replications`, `seed` |
| `root_cause_result` | `scope_type`, `scope_id`, `problem`, `cause`, `evidence_json`, `confidence`, `recommended_action`, `expected_impact_json`, `created_at` |
| `recommendation` | `id`, `type`, `status` (`PROPOSED, VALIDATED, REJECTED_BY_CHECK, APPLIED, DISMISSED`), `problem/cause/evidence/confidence/action/impact` (JSON), `checks_json` (V1–V8 results), `sim_before_after_json`, `created_at`, `applied_by`, `applied_at` |
| `schedule_plan` | `id`, `solver_status`, `gap`, `objective_json`, `quantile_used`, `horizon_start/end`, `created_at`, `parent_plan_id` |
| `schedule_assignment` | `plan_id`, `component_unit_id`, `workstation_id`, `worker_ids[]`, `start`, `end` |
| `alert` | `type`, `scope_type`, `scope_id`, `severity`, `message`, `evidence_json`, `raised_at`, `ack_by`, `ack_at`, `resolved_at` |
| `model_run` | `model_name`, `version`, `status` (`CHAMPION, CHALLENGER, PROMOTED, REJECTED, ROLLED_BACK`), `train_range`, `features_json`, `params_json`, `metrics_json`, `trigger` |
| `sim_session` | `id`, `kind` (`WHATIF, REPLAY`), `snapshot_ref`, `seed`, `events_json`, `clock`, `created_by` — **sandbox only, never live tables** |

## 5. Ground truth (synthetic only; evaluation only)

| Table | Content |
|---|---|
| `gt_latent_traits` | worker `skill_true`, worker `learning_rate`, workstation `speed_factor`, workstation `mtbf/mttr`, component `complexity` |
| `gt_scenario_label` | `scenario_id`, `injected_cause`, `scope`, `start`, `end` |

**Never** expose these to feature pipelines. A CI test greps the ML feature list for any `gt_*` column.

## 6. Key views / read models (for fast UI)

- `v_component_board(dept_id)` — per component *type*: counts by status, hours-weighted progress, expected/P75/P90 finish, avg std-vs-actual hours, blocked reasons.
- `v_loom_progress` — per loom unit: stage, progress, blocking component, predicted completion.
- `v_dept_workforce(dept_id, shift_window)` — rostered/present/absent, loans in/out, skills coverage.
- `v_ready_queue(dept_id)` — READY units sorted by priority/due date.
- `v_kit_status` — per loom unit × feeder dept: complete/partial.

## 7. Integrity rules / required tests

- FK integrity; Alembic upgrade on empty DB clean; downgrade works for latest revision.
- `component_prerequisite` is acyclic (loader + DB constraint-check test).
- Every `component_type` has ≥ 1 eligible workstation type with ≥ 1 workstation and ≥ 1 qualified worker (at seed time).
- `component_unit` event stream is a legal walk of the state machine (property test on generated data).
- A worker is never on two units at the same time; a workstation never runs two units (except configured multi-slot).
- Dept progress = hours-weighted formula; counts per status sum to total units.
- `rebuild_projection()` ≡ live projection.
- No code path writes `component_unit` or `component_event` from within a `sim_session`.
