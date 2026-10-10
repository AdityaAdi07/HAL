# 04 — Frontend & 3D Digital Twin

> Next.js (App Router) + strict TypeScript + `@react-three/fiber` + `@react-three/drei` + Zustand + TanStack Query + Recharts + Tailwind. Types generated from the FastAPI OpenAPI schema (`openapi-typescript`). Aesthetic: **dark industrial control room** (carried over from the handloom UI) with a light/dark toggle.

---

## 1. The core interaction (the headline requirement)

> **A 3D factory with 5 department pods. Click a department → see the components it is building with their status, progress, capacity, load, predictions, and workers/shifts. Not the building process.**

```
 FACTORY VIEW  ──click pod──►  DEPARTMENT VIEW  ──click component tile──►  COMPONENT DRAWER
      ▲                              │                                          │
      └──────── Esc / Back ◄─────────┘◄──────────────── Esc ◄───────────────────┘
```

URL-addressable: `/twin` (factory), `/twin/DEPT-FAB` (department), `/twin/DEPT-FAB?component=FAB-HEDDLE` (drawer open). Browser back/forward work. Deep links restore camera + selection.

---

## 2. Factory view (`/twin`)

### 2.1 Scene layout

```
            ┌─ DEPT-MECH ─┐         ┌─ DEPT-SENS ─┐
  inbound   │  (1)        │ ──►     │  (3)        │ ──►        ┌──────────────────┐
  material  └─────────────┘   kit   └─────────────┘   kit      │                  │
            ┌─ DEPT-FAB ──┐  buffers┌─ DEPT-PWR ──┐ buffers    │   DEPT-ASSY (5)  │ ──► dispatch
            │  (2)        │ ──►     │  (4)        │ ──►        │  Assembly &      │
            └─────────────┘         └─────────────┘            │  Integration     │
                                                               └──────────────────┘
```

- Positions come from `department.layout_json` (seeded from `catalog.yaml`). **No hard-coded coordinates in component code.**
- **Flow lanes** between pods are static chevron lines (direction of kit flow). Each lane ends at a **kit-buffer shelf** object showing the **count of completed, ready-to-consume components** staged for assembly (e.g. `MECH → ASSY: 11 ready`). Chevron shimmer speed may scale with recent throughput. **No component sprites travelling and no assembly animation.**
- Floor: grid, labels, subtle zone outline per pod.

### 2.2 Pod (department) visual

Each pod is a procedural platform with:

| Element | Encodes |
|---|---|
| **Load tower** (vertical bar, height ∝ `min(load_expected, 150)%`, tick marks at 70/95) with P75/P90 ghost caps | Expected/P75/P90 load |
| **Progress ring** around the base | Hours-weighted department progress for active orders |
| **Status badge** (HTML overlay via drei `<Html>`, limited to 5) | Text `OVERLOAD_RISK` etc. + icon + `STARVED`/`SHORT_STAFFED` chips |
| **Bottleneck marker** (hazard-stripe frame + "BOTTLENECK" label) | System/second bottleneck |
| **Worker pips** (small instanced figures count = present workers this shift; hollow = absent) | Staffing |
| Name plate | `1 · Mechatronics`, etc. |

Status is **never colour only**: every state has icon + text + pattern (see §6).

### 2.3 Factory overlay (HTML, over the canvas)

- **Top bar:** clock (live or sim), mode toggle `LIVE | SIMULATION`, current shift + time remaining, `data_source` badge (`SYNTHETIC`/`LIVE`).
- **KPI strip:** system throughput (looms/day) vs demand, on-time probability, active/blocked/late looms, current system bottleneck.
- **Loom pipeline strip (bottom):** chips for active loom units grouped by stage (`COMPONENT BUILD → KIT COMPLETE → ASSEMBLY → TEST → DONE`). Click a chip → **Trace mode**: that loom becomes the selection; every pod and tile highlights *that loom's* component states (non-selected looms dim). Esc clears. Search box by serial.
- **Alerts tray** (right): latest alerts, severity icon + text, click → focuses scope.

---

## 3. Department view (`/twin/[deptCode]`)

Camera eases (≈0.8 s, `prefers-reduced-motion` ⇒ instant cut) to the pod; other pods fade to 25%. The pod "opens" into a **component board**.

### 3.1 Component board (3D, state only)

One **tile per component type** owned by the department (e.g. MECH → 6 tiles, ASSY → 8 stage tiles), arranged in a grid driven by `sequence_hint` and prerequisites (arrows between tiles within the dept for prereqs).

Each tile contains:
- A **3D representation of the component** from the **visual registry** (`visual_key` → procedural primitive recipe; see §7). Static or gently idle-rotating only while `IN_PROGRESS` (reduced-motion ⇒ static).
- **Name** + code.
- **Status badge** (dominant state of its units: text + icon).
- **Progress bar** (hours-weighted % across active units) + `done/total` (e.g. `14 / 20`) and mini stacked count chips: `✓ done · ▶ in progress · ⏱ queued · 🔎 QC · ⚠ blocked`.
- **Predicted finish** (`Exp / P75 / P90` for the last unit of the current batch).
- **Assigned workstations** (short list) and **blocked reason** chip if any.
- **Std vs actual** micro-indicator (`std 2.0h · actual avg 2.3h`).

Tile interaction: hover → tooltip with the above; click → **Component drawer**. Keyboard: arrow keys move focus across tiles, Enter opens drawer, Esc closes.

### 3.2 Component drawer

Table of **ComponentUnits** for that type: loom serial, status, progress, workstation, worker(s), planned vs actual start/end, expected/P75/P90, rework count, block reason; filter by loom / status / shift; click row → highlights that loom in Trace mode. Tabs: `Units · Timeline · Quality (FPY, rework) · Materials · History (events)`.

### 3.3 Department side panel (persistent, right side, HTML)

Header (always visible): dept name, **load class badge**, load tower mini (Exp/P75/P90), progress %, current shift + ends-in.

Tabs:

1. **Overview** — progress (hours-weighted + counts), WIP by status, ready queue length, bottleneck flag, root cause card (Problem/Cause/Evidence/Confidence/Action/Impact).
2. **Capacity** — current shift / today / this week cards: theoretical → scheduled → available → usable (waterfall bar), efficiency, material factor, looms/day throughput; workstation list with status (`AVAILABLE/IN_USE/DOWN/MAINTENANCE`) and utilisation.
3. **Load** — gauges for Expected/P75/P90 with threshold markers (70/95 from config), stress load, capacity balance (h), 7-day load strip (per-day load class).
4. **Prediction** — (a) workload forecast chart: history + Expected line + P75/P90 band, horizon toggle 7D/30D/90D; (b) capacity forecast: expected vs pessimistic; (c) component finish predictions table; (d) **loom completion**: next 5 looms' completion distribution + on-time probability; (e) model badge: version, last backtest coverage, `fallback_used` note.
5. **Workforce & Shifts** — see §3.4.
6. **Balancing** — recommendations list (status, type, Problem/Cause/Evidence/Confidence/Action/Impact, `checks` V1–V8 with ✓/✗, simulated before/after/delta); buttons `Simulate`, `Apply` (role-gated, confirm dialog stating "this changes the *plan*, not actuals"), `Dismiss`.

### 3.4 Workforce & Shifts tab

- **Shift selector:** `Current | Next | Today | Tomorrow | Week`.
- **Roster table:** worker, home dept, **rostered here (REGULAR/OVERTIME/LOAN-in)**, shift, availability (`PRESENT/ABSENT/LEAVE/LATE`), current workstation, current component unit, skills (chips with level), utilisation %.
- **Loans:** workers lent *out* (to which dept) and lent *in* (from where) shown distinctly.
- **Shift timeline (Gantt, 2D):** rows = workers, columns = hours across selected days; bars = tasks (component codes) and breaks; gaps = idle; absent = hatched.
- **Skill coverage matrix:** skills required by the dept's component types × shifts → count of qualified present workers vs required; `SKILL_BOUND` warning when ≤ 1 qualified worker covers a skill that has queued work.
- No names/photos required; worker `code` is enough (privacy-minimal by default; `name` shown to `supervisor+` roles).

---

## 4. Other routes

```
/dashboard                 factory KPIs, system throughput vs demand, dept load grid, bottleneck, late looms, alerts
/twin, /twin/[deptCode]    §2–§3
/looms                     loom tracker table (filter by order/model/stage/status/late) + stage pipeline
/looms/[serial]            Loom passport (see §5)
/orders, /orders/[code]    loom build orders, progress, forecasted completion, on-time probability
/capacity                  department tree: capacity cards, Expected/P75/P90 workload & load, class, root cause
/load-balancing            all recommendations across depts; filters; apply/simulate
/forecast                  workload & capacity forecasts; horizons 7/30/90; filters Factory/Dept/Component
/workforce                 all workers, skills matrix, rosters, leave/absence, loan history
/materials                 inventory, requirements vs availability, blocked components
/what-if                   scenario builder → simulation → before/after/delta → recommended action
/alerts                    list + thresholds config + email notification settings (carried from handloom)
/models, /models/health, /models/retraining   build-time model + forecast monitoring, drift, champion/challenger
/pipeline                  data flow & engine status
/terminal/[deptCode]       lightweight station terminal: start/progress/complete/QC/block events (manual data entry)
/settings                  thresholds, shifts, weights, catalog viewer, data_source, theme
```

---

## 5. Loom passport (`/looms/[serial]`) — "track the manufacturing of a loom"

- Header: serial, model, order, priority, due date, **overall progress (hours-weighted)**, current stage, **predicted completion Exp/P75/P90 + on-time probability**, `blocking component`.
- **Stage ribbon:** `Components → Kit complete → Frame → Mech install → Fabric install → Power → Sensors → Calibration → Test → Pack` with state per stage (icon + text).
- **Component grid (32 chips)** grouped by department; each chip = status badge + progress + date. Late/blocked chips float to top. *(State only; no assembly animation.)*
- **Critical path highlight:** the chain of units currently determining completion.
- Timeline of events (`component_event`) with planned-vs-actual deltas.
- Button **"Show in 3D"** → `/twin?trace=<serial>`.

---

## 6. Status visual language (accessibility is a requirement)

| State | Icon | Text | Pattern / motion (never the only cue is colour) |
|---|---|---|---|
| `NOT_STARTED` | dashed circle | NOT STARTED | outline only |
| `QUEUED` | clock | QUEUED | dotted border |
| `IN_PROGRESS` | play | IN PROGRESS | progress ring + slow pulse |
| `IN_QC` | magnifier-check | IN QC | scan-line shimmer |
| `REWORK` | rotate-ccw | REWORK | diagonal stripe |
| `BLOCKED` | octagon-alert | BLOCKED (reason) | hazard-stripe + slow blink (≤ 1 Hz) |
| `COMPLETED` | check-circle | DONE | solid fill |
| `REJECTED` | x-circle | REJECTED | strike-through |
| `UNDERLOAD` | arrow-down-circle | UNDERLOAD | low tower |
| `HEALTHY` | check | HEALTHY | — |
| `OVERLOAD_RISK` | triangle-alert | OVERLOAD RISK | dashed ghost cap above tower |
| `OVERLOAD` | flame / alert-octagon | OVERLOAD | hazard frame + pulse |
| `UNAVAILABLE` | ban | UNAVAILABLE | hatched |

Colour tokens are supplemental. `prefers-reduced-motion` disables pulses/blinks/camera easing (replace with static emphasis). Provide `aria-label`s containing the same text as the badge. Charts have a data-table toggle. All controls are keyboard reachable; focus ring visible.

---

## 7. Visual registry (procedural components)

`src/twin/visuals/registry.ts` maps `visual_key` → factory `(params) => THREE.Group` built from primitives, with a `fallback_box`. **Adding a component type in `catalog.yaml` must not require code changes** (it falls back to a labelled box). Defaults:

| visual_key | Primitive recipe |
|---|---|
| `motor` | cylinder body + shaft cylinder + 2 end caps |
| `driver_box` | box + small heat-fin boxes + LED dot |
| `coupling` | two short cylinders + torus ring |
| `sprocket` | flat cylinder with N small boxes around rim |
| `chain_loop` | torus of small boxes (instanced) |
| `tensioner` | arm box + spring (thin cylinder) + wheel |
| `beam_large` / `beam_small` | long cylinder + two flange discs (diameter differs) |
| `heddle_frames` | 3 thin rectangular frames (box outlines) in a row |
| `reed_comb` | row of thin boxes (instanced) in a frame |
| `rollers` | 3 parallel cylinders |
| `bobbin_rack` | rack box + cones (cylinders with taper) |
| `pcb_small` / `pcb_ring` / `pcb_chip` / `pcb_hub` | thin green-neutral box + chip box(es) / ring |
| `load_cell` | metal bar box + strain-gauge patch + cable |
| `inlet_panel` | panel box + socket cylinder + breaker blocks |
| `psu_box` / `controller` / `meter` | box + vent slats / display plane |
| `harness` | tube curve (CatmullRom) with connector boxes |
| `frame` | extruded rectangular frame from box beams |
| `install_*`, `calib`, `test_rig`, `crate` | simplified stage icons (frame + highlighted sub-part) |

Rules: **instancing** when > 20 identical meshes (reed teeth, chain links, worker pips); share geometries/materials; **dispose** geometries, materials, textures on unmount; target 60 fps on a mid laptop with all pods mounted; level-of-detail: only the selected department's tiles use full detail, others use a single low-poly proxy.

---

## 8. State, data flow, events

- **Zustand stores** (ported/adapted from `sandbox/core/SandboxState.js`): `useTwinStore` (selected dept/component/loom, camera target, trace mode, mode LIVE/SIM, clock), `useUiStore` (theme, panels, filters).
- **Server state:** TanStack Query for REST; WebSocket updates call `queryClient.setQueryData` / invalidate narrowly.
- **One** WebSocket connection via a provider; messages dispatched on the **event bus** (ported from `EventBus.js` to TS). The 3D scene subscribes to the bus (not to React state) for high-frequency updates; React panels subscribe to the query cache.
- **Event types consumed:** `component.status_changed`, `component.progress`, `loom.stage_changed`, `dept.metrics_updated`, `workforce.shift_changed`, `worker.availability_changed`, `alert.raised`, `recommendation.created`, `sim.clock`.
- **Mode isolation:** `LIVE` reads live endpoints; `SIMULATION` reads `/api/sim/{session_id}/...`. The mode badge is always visible; simulation sessions never write to live (enforced server-side; UI also disables `Apply` for sim-only data unless explicitly promoting a recommendation).

---

## 9. Frontend tests (Vitest + Playwright)

- Unit: status → badge mapping covers every enum value; visual registry fallback; load-class → tower/badge; shift-time formatting.
- Component: dept panel renders all 6 tabs with fixture data; blocked tile shows reason text (not only colour).
- E2E (Playwright): (1) load `/twin`, 5 pods rendered with text badges; (2) click `DEPT-FAB` → URL changes, component tiles appear, panel shows capacity/load/prediction/workforce; (3) click a tile → drawer lists units; (4) Trace a loom serial → highlights; (5) Esc returns to factory; (6) reduced-motion media emulation disables pulses; (7) simulation mode never changes live KPIs after injecting an event; (8) keyboard-only navigation reaches a tile and opens its drawer.
- Visual smoke test: canvas not blank (non-zero pixel variance), no console errors.
