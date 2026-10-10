# 01 — Domain: Departments, Components, Precedence, Workforce

> Read with root `CLAUDE.md`. Everything here is **data** loaded from `configs/catalog.yaml` and `configs/factory.yaml`. Code must never hard-code a component, department size, or shift number.

---

## 1. Product model

- **LoomModel** — a product variant (e.g. `LM-100`). Has a **bill of components** (`LoomModelComponent`: component type + `qty_per_loom` + `complexity_multiplier`).
- **LoomBuildOrder** — a customer/internal order: *N* looms of a model, with priority, release date, due date.
- **LoomUnit** — one physical loom (serial `LM100-000123`). Created when an order is released.
- **ComponentUnit** — one instance of a component type that belongs to one loom unit. **This is the thing we track.** (A loom with `SENS-LOAD × 2` has two ComponentUnits for that type.)

A loom is *complete* when its final assembly stage (`ASY-PACK`) is `COMPLETED`.

---

## 2. Departments

| No. | Code | Name | Colour token (supplemental only) | Accent icon key |
|---|---|---|---|---|
| 1 | `DEPT-MECH` | Mechatronics | `--dept-mech` | `cog` |
| 2 | `DEPT-FAB` | Fabrics | `--dept-fab` | `spool` |
| 3 | `DEPT-SENS` | Sensors | `--dept-sens` | `radar` |
| 4 | `DEPT-PWR` | Power Optimization & Inlet | `--dept-pwr` | `bolt` |
| 5 | `DEPT-ASSY` | Assembly & Integration | `--dept-assy` | `wrench` |

Each department has: a layout position (3D), a lead (worker), a pool of **workstations**, a pool of **workers**, and a set of **component types**.

---

## 3. Component catalog (defaults; hours are *standard* hours per unit)

`std_h` = planned/standard build time (the planner's number). Actual differs systematically by worker skill, workstation, learning, complexity — that gap is what the ML model learns. `crew` = workers needed simultaneously. `WS` = eligible workstation types. `Skill` = `SKILL(min_level)`.

### 3.1 DEPT-MECH — Mechatronics (chain & motor)

| Code | Name | std_h | qty/loom | Skill | WS | Prereqs (within dept) | visual_key |
|---|---|---|---|---|---|---|---|
| `MECH-MOTOR` | Drive motor assembly | 2.0 | 1 | SK-MOTOR(3) | MOTOR_BENCH | — | `motor` |
| `MECH-DRIVER` | Motor driver/controller unit | 1.8 | 1 | SK-ELEC-WIRING(3) | ELEC_TEST_BENCH | — | `driver_box` |
| `MECH-COUPLING` | Coupling & motor mount bracket | 1.0 | 1 | SK-MECH(2) | DRIVE_ASSY_BENCH, MOTOR_BENCH | MECH-MOTOR | `coupling` |
| `MECH-SPROCKET` | Sprocket & shaft set | 1.2 | 1 | SK-MECH(2) | DRIVE_ASSY_BENCH | — | `sprocket` |
| `MECH-CHAIN` | Chain drive assembly | 1.5 | 1 | SK-MECH(2) | DRIVE_ASSY_BENCH | MECH-SPROCKET | `chain_loop` |
| `MECH-TENSIONER` | Chain tensioner | 0.8 | 1 | SK-MECH(2) | DRIVE_ASSY_BENCH | — | `tensioner` |

### 3.2 DEPT-FAB — Fabrics (thread & fibre path)

| Code | Name | std_h | qty/loom | Skill | WS | Prereqs | visual_key |
|---|---|---|---|---|---|---|---|
| `FAB-WARPBEAM` | Warp beam assembly | 2.5 | 1 | SK-FAB-ASSY(2) | BEAM_ASSY_STATION | — | `beam_large` |
| `FAB-CLOTHBEAM` | Cloth (take-up) beam | 2.0 | 1 | SK-FAB-ASSY(2) | BEAM_ASSY_STATION | — | `beam_small` |
| `FAB-HEDDLE` | Heddle frame set (shafts + healds) | 3.0 | 1 | SK-PRECISION(3) | HEDDLE_REED_JIG | — | `heddle_frames` |
| `FAB-REED` | Reed & beat-up assembly | 2.2 | 1 | SK-PRECISION(3) | HEDDLE_REED_JIG | — | `reed_comb` |
| `FAB-THREADGUIDE` | Thread guide & tension roller set | 1.5 | 1 | SK-FAB-ASSY(2) | THREAD_PATH_BENCH | — | `rollers` |
| `FAB-WEFT` | Weft bobbin/cone holder set | 1.0 | 1 | SK-FAB-ASSY(1) | THREAD_PATH_BENCH | — | `bobbin_rack` |

### 3.3 DEPT-SENS — Sensors

| Code | Name | std_h | qty/loom | Skill | WS | Prereqs | visual_key |
|---|---|---|---|---|---|---|---|
| `SENS-TEMP` | Temperature sensor module | 0.5 | 1 | SK-SOLDER(2) | SOLDER_STATION | — | `pcb_small` |
| `SENS-HUM` | Humidity sensor module | 0.5 | 1 | SK-SOLDER(2) | SOLDER_STATION | — | `pcb_small` |
| `SENS-RPM` | RPM sensor (hall/IR) module | 0.7 | 1 | SK-SOLDER(2) | SOLDER_STATION | — | `pcb_ring` |
| `SENS-IMU` | **MPU6050** vibration/IMU module | 0.8 | 1 | SK-SOLDER(3) | SOLDER_STATION, SENSOR_CAL_BENCH | — | `pcb_chip` |
| `SENS-LOAD` | **Load sensor** (cell + amplifier) module | 1.2 | **2** (warp & cloth tension) | SK-SENSOR-CAL(3) | SENSOR_CAL_BENCH | — | `load_cell` |
| `SENS-HUB` | Sensor hub board (MCU) & harness | 1.5 | 1 | SK-FIRMWARE(2) | HARNESS_BENCH, SOLDER_STATION | — | `pcb_hub` |

### 3.4 DEPT-PWR — Power Optimization & Inlet

| Code | Name | std_h | qty/loom | Skill | WS | Prereqs | visual_key |
|---|---|---|---|---|---|---|---|
| `PWR-INLET` | Power inlet & protection panel | 1.2 | 1 | SK-PWR-ELEC(2) | POWER_ASSY_BENCH | — | `inlet_panel` |
| `PWR-PSU` | Regulated PSU module | 1.0 | 1 | SK-PWR-ELEC(2) | POWER_ASSY_BENCH | — | `psu_box` |
| `PWR-METER` | Energy metering module | 0.8 | 1 | SK-ELEC-WIRING(2) | POWER_ASSY_BENCH | — | `meter` |
| `PWR-OPT` | Power optimization controller | 2.0 | 1 | SK-PWR-ELEC(3) | POWER_ASSY_BENCH, HV_TEST_BENCH | PWR-PSU | `controller` |
| `PWR-HARNESS` | Main power harness | 1.5 | 1 | SK-ELEC-WIRING(2) | HARNESS_BENCH | PWR-INLET, PWR-PSU | `harness` |

### 3.5 DEPT-ASSY — Assembly & Integration (stages are components too)

Assembly *stages* are modelled as component types with **cross-department prerequisites**. This unifies precedence handling: one DAG, one readiness rule.

| Code | Name | std_h | crew | Skill | WS | Prereqs (cross-dept shown) | visual_key |
|---|---|---|---|---|---|---|---|
| `ASY-FRAME` | Frame & chassis build | 4.0 | 2 | SK-FINAL-ASSY(2) | ASSEMBLY_BAY | — | `frame` |
| `ASY-MECH` | Mechatronics install | 2.5 | 1 | SK-FINAL-ASSY(3) | ASSEMBLY_BAY | ASY-FRAME + **all MECH-\*** | `install_mech` |
| `ASY-FABRIC` | Fabric-path install | 3.5 | 1 | SK-FINAL-ASSY(3) | ASSEMBLY_BAY | ASY-MECH + **all FAB-\*** | `install_fab` |
| `ASY-POWER` | Power integration | 2.0 | 1 | SK-ELEC-WIRING(3) | ASSEMBLY_BAY | ASY-MECH + **all PWR-\*** | `install_pwr` |
| `ASY-SENSOR` | Sensor integration | 2.0 | 1 | SK-SENSOR-CAL(2) | ASSEMBLY_BAY | ASY-FABRIC, ASY-POWER + **all SENS-\*** | `install_sens` |
| `ASY-CALIB` | Calibration & firmware | 2.0 | 1 | SK-CALIB(3) | CALIB_STATION | ASY-SENSOR | `calib` |
| `ASY-TEST` | End-of-line test & QC | 2.5 | 1 | SK-QC(3) | TEST_RIG | ASY-CALIB | `test_rig` |
| `ASY-PACK` | Packaging & dispatch prep | 1.0 | 1 | SK-FINAL-ASSY(1) | PACK_STATION | ASY-TEST | `crate` |

**Per-loom standard hours (LM-100):** MECH 8.3 · FAB 12.2 · SENS 6.4 · PWR 6.5 · ASSY 19.5 → **52.9 h** over **32 component units** (`SENS-LOAD` ×2).

### 3.6 Precedence DAG (summary)

```
MECH-* ─────────────► ASY-MECH ─┬─► ASY-FABRIC ◄── FAB-*
PWR-*  ─────────────►           └─► ASY-POWER  ◄── PWR-*
        ASY-FRAME ──► ASY-MECH
SENS-* ─────────────► ASY-SENSOR ◄── ASY-FABRIC, ASY-POWER
ASY-SENSOR → ASY-CALIB → ASY-TEST → ASY-PACK
```

Rules:
- Graph must be **acyclic** (validated at seed time; fail loudly).
- A `ComponentUnit` is **READY** when every prerequisite unit **of the same loom unit** is `COMPLETED` (QC passed) and (if configured) its inbound transfer buffer delay has elapsed.
- Optional config `kit_lead_limit`: max loom units a feeder dept may build *ahead* of assembly's current loom (WIP cap). Prevents Depts 1–4 hoarding hours on looms Assembly can't reach.
- Optional `transfer_time_h` per (from_dept → to_dept).

---

## 4. Skills, workstation types, workers

### 4.1 Skills (default 12; the list lives in config, not code)

`SK-MECH, SK-MOTOR, SK-FAB-ASSY, SK-PRECISION, SK-SOLDER, SK-SENSOR-CAL, SK-FIRMWARE, SK-ELEC-WIRING, SK-PWR-ELEC, SK-CALIB, SK-QC, SK-FINAL-ASSY`

Levels 1–5. A worker is **qualified** for a component if `worker_skill.level ≥ component.required_level` and the certification is valid on that date.

**Cross-training (intentional overlap that enables load balancing):**
- `SK-SOLDER` + `SK-ELEC-WIRING`: Sensors ↔ Power ↔ Mechatronics(driver) ↔ Assembly(power integration)
- `SK-MECH`: Mechatronics ↔ Fabrics ↔ Assembly
- `SK-QC`: held by a few in every department (also does in-process QC)
- Only ~15–25% of workers hold a skill outside their home department. Lending is possible **only** through these overlaps.

### 4.2 Workstation types and counts (default)

| Dept | Types (count) |
|---|---|
| MECH | `MOTOR_BENCH`(2), `DRIVE_ASSY_BENCH`(3), `ELEC_TEST_BENCH`(1) |
| FAB | `BEAM_ASSY_STATION`(2), `HEDDLE_REED_JIG`(3), `THREAD_PATH_BENCH`(3) |
| SENS | `SOLDER_STATION`(2), `SENSOR_CAL_BENCH`(2), `HARNESS_BENCH`(1) |
| PWR | `POWER_ASSY_BENCH`(3), `HV_TEST_BENCH`(1), `HARNESS_BENCH`(1) |
| ASSY | `ASSEMBLY_BAY`(5), `CALIB_STATION`(1), `TEST_RIG`(2), `PACK_STATION`(1) |

Deliberately **not dense**: several component types have exactly one eligible workstation type with 1–2 units (`ELEC_TEST_BENCH`, `HV_TEST_BENCH`, `CALIB_STATION`) → natural bottlenecks that make balancing meaningful.

### 4.3 Workers and shifts (defaults)

| Item | Default |
|---|---|
| Shifts | `SHIFT-A` 06:00–14:00, `SHIFT-B` 14:00–22:00; 0.5 h break → **7.5 productive h** |
| Working days | Mon–Fri; ~12–15 holidays/yr; 1–2 planned shutdown weeks |
| Max scheduled h / worker / day | 8 (+ configurable overtime ≤ 2 h) |
| Max shifts / worker / day | 1 (overtime counts as extension, not a second shift) |
| Headcount | MECH 8, FAB 12, SENS 6, PWR 7, ASSY 18 = 51 (≈ half per shift; roster rotates weekly) |
| Absence | ~3–6% random daily; planned leave from calendar |
| Skills per worker | 1–4, levels 1–5 |

---

## 5. State machines

### 5.1 ComponentUnit

```
NOT_STARTED ─► QUEUED ─► IN_PROGRESS ─► IN_QC ─► COMPLETED
                  ▲           │  ▲         │
                  │           ▼  │         ├─► REWORK ─► IN_PROGRESS
                  └────── BLOCKED ┘         └─► REJECTED  (spawns replacement unit; links replaces_id)
```

| Status | Meaning | Icon | Text badge |
|---|---|---|---|
| `NOT_STARTED` | Released, prerequisites not met | `circle-dashed` | NOT STARTED |
| `QUEUED` | READY, waiting for worker/workstation | `clock` | QUEUED |
| `IN_PROGRESS` | Being built now | `play-circle` | IN PROGRESS |
| `IN_QC` | In-process inspection | `search-check` | IN QC |
| `REWORK` | QC failed, fixable | `rotate-ccw` | REWORK |
| `BLOCKED` | Cannot proceed (see `block_reason`) | `octagon-alert` | BLOCKED |
| `COMPLETED` | QC passed, available to downstream | `check-circle` | DONE |
| `REJECTED` | Scrapped | `x-circle` | REJECTED |

`block_reason`: `MATERIAL`, `WORKER_UNAVAILABLE`, `SKILL_GAP`, `WORKSTATION_DOWN`, `UPSTREAM_PREREQ`, `QC_HOLD`, `OTHER`.

Illegal transitions are rejected by the state machine (unit-tested table). `COMPLETED → anything` is forbidden except an audited `REOPEN` event.

### 5.2 Progress

- `progress_pct` is derived from events. If a worker/terminal **reports** progress, use it (`progress_source = REPORTED`). Otherwise estimate `min(0.95, worked_h / expected_h)` (`ESTIMATED`). Only `COMPLETED` is 100%.
- **Department progress** = Σ(std hours of COMPLETED units + progress × std hours of open units) ÷ Σ(std hours of all units in active orders). **Hours-weighted, not count-weighted.** Also display counts.

### 5.3 LoomUnit

`PLANNED → IN_COMPONENT_BUILD → KIT_PARTIAL → KIT_COMPLETE → IN_ASSEMBLY → IN_TEST → COMPLETED` (+ `ON_HOLD`, `CANCELLED`).
Derived: `stage` (from furthest-completed ASY-*), `progress_pct` (hours-weighted over its units), `blocking_component` (earliest unfinished critical-path unit), `predicted_completion {expected,p75,p90}`, `on_time_probability`.

### 5.4 Department status (derived, for the 3D pod badge)

Load class: `UNDERLOAD | HEALTHY | OVERLOAD | OVERLOAD_RISK | UNAVAILABLE` plus flags `STARVED` (idle because prerequisites/WIP cap), `BLOCKED_BY_MATERIAL`, `SHORT_STAFFED`.

---

## 6. `catalog.yaml` shape (excerpt)

```yaml
version: 1
skills:
  - {code: SK-SOLDER, name: Soldering}
  - {code: SK-ELEC-WIRING, name: Electrical wiring}
workstation_types:
  - {code: SOLDER_STATION, dept: DEPT-SENS}
departments:
  - code: DEPT-SENS
    no: 3
    name: Sensors
    layout: {x: -8, z: 6}            # consumed by frontend; may be overridden in DB
components:
  - code: SENS-IMU
    dept: DEPT-SENS
    name: MPU6050 vibration/IMU module
    std_h: 0.8
    crew: 1
    required_skill: {code: SK-SOLDER, min_level: 3}
    workstation_types: [SOLDER_STATION, SENSOR_CAL_BENCH]
    prerequisites: []
    material_lines: [{material: MAT-MPU6050, qty: 1, scrap: 0.03}]
    first_pass_yield: 0.96
    visual_key: pcb_chip
  - code: ASY-SENSOR
    dept: DEPT-ASSY
    prerequisites: [ASY-FABRIC, ASY-POWER, "dept:DEPT-SENS:*"]   # wildcard = all component types of that dept
loom_models:
  - code: LM-100
    components: {all: 1, overrides: {SENS-LOAD: 2}}
    complexity: 1.0
```

Loader responsibilities: expand wildcards, validate acyclic DAG, verify every component has ≥1 eligible workstation type with ≥1 workstation and ≥1 qualified worker (warn if exactly 1), write to DB idempotently (upsert on code).

---

## 7. Materials (kept deliberately light)

`Material` (e.g. `MAT-MPU6050`, `MAT-HX711`, `MAT-LOADCELL`, `MAT-COPPER-WIRE`, `MAT-STEEL-CHAIN`, `MAT-MOTOR-CORE`, `MAT-REED-STEEL`, `MAT-FRAME-ANGLE`) with `Inventory` (available, reserved, incoming, expected arrival, safety stock) and `BOM` lines per component type (qty + scrap factor). Chain: `ComponentType → BOM → requirement → available → reserved → incoming → shortage`. A unit with a shortage becomes `BLOCKED(MATERIAL)` and lowers the dept's material-availability factor. Materials are not a separate 3D scene; surface them as a status chip and a Materials panel.
