# HAL — Powerloom Manufacturing Digital Twin

[![CI Backend Tests](https://img.shields.io/badge/pytest-28%2F28%20passed-brightgreen.svg)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.111-teal.svg)]()
[![Next.js](https://img.shields.io/badge/Next.js-15.5-black.svg)]()
[![React Three Fiber](https://img.shields.io/badge/R3F-3D%20Digital%20Twin-orange.svg)]()

> **Powerloom Manufacturing Digital Twin: Component Tracking · Capacity & Load Intelligence · CP-SAT Balancing · Quantile ML Prediction · 3D Control Twin**

---

## 📌 1. Overview & Reframing

HAL models a **complete 5-department factory that manufactures industrial powerlooms**. Each loom consists of ~32 components produced across four parallel feeder departments and finalized in assembly.

The 3D digital twin is a live representation of real-time manufacturing state, component queues, workstation capacity, operator allocation, and bottlenecks.

### The Five Factory Departments

| No. | Department Code | Department Name | Scope & Responsibilities | Key Components |
|:---:|---|---|---|---|
| 1 | `DEPT-MECH` | **Mechatronics** | Drive motors, speed controllers, chain drives, sprockets | Drive Motor, Motor Driver, Chain, Tensioner |
| 2 | `DEPT-FAB` | **Fabrics** | Thread path, beams, shedding mechanism | Warp Beam, Heald Wires, Reed Comb, Shuttle Box |
| 3 | `DEPT-SENS` | **Sensors** | Telemetry, load cells, optical sensors, hub | Tension Load Cell, Optical Detector, Rotary Encoder, Thermal Probe |
| 4 | `DEPT-PWR` | **Power Optimization & Inlet** | Industrial power supplies, safety circuits, metering | Industrial PSU (24V/15A), Power Dist Board, E-Stop, Wiring Harness |
| 5 | `DEPT-ASSY` | **Assembly & Integration** | Final integration of parallel feeds, QA, calibration | Loom Chassis, Mechatronics Mount, Warp Beam Mount, Calibration, QA Run |

---

## 🎯 2. Core Capabilities

1. **Component Tracking**: Every Bill of Materials (BOM) unit has append-only event tracking, status, progress %, workstation, worker, and predicted completion time.
2. **Loom Build Tracking**: Hours-weighted progress aggregation across all ~32 component units per loom unit serial.
3. **Capacity & Load Intelligence**: Theoretical $\to$ Scheduled $\to$ Available $\to$ Usable capacity computation with Monte-Carlo aggregation ($P90_{\text{agg}} < \sum P90$).
4. **Automated Root Cause Diagnostics**: Distinguishes between Underload ($<70\%$), Healthy ($70\% - 95\%$), Overload ($>95\%$), and Overload Risk ($P75 > 95\%$). Detects upstream starvation and worker absence.
5. **Load Balancing & Optimization**: Google OR-Tools CP-SAT discrete optimization combined with SimPy simulation to validate reassignment recommendations across V1–V8 constraint checks.
6. **Machine Learning Predictions**: LightGBM quantile regressors ($P50, P75, P90$) for build-time estimation and Holt-Winters time-series forecasters for multi-horizon workload projection.
7. **Production Monitoring & Drift**: Population Stability Index (PSI) tracking, model drift alarms, and champion/challenger retraining governance with automated rollback.
8. **3D Interactive Digital Twin**: Built with React Three Fiber and Three.js featuring 5 procedural pods, moving material flow chevrons, live component mesh viewers, and complete Dark/Light mode support.

---

## 🧠 3. Planner's Decision Loop

HAL continuously answers the eight core operational questions:

```
SENSE ➔ UNDERSTAND ➔ PREDICT ➔ EXPLAIN ➔ DECIDE ➔ OPTIMIZE ➔ SIMULATE ➔ EXECUTE ➔ LEARN
```

1. **Can we deliver upcoming loom orders on time?**  
   *Real-time on-time probability with risk classification (e.g. 73% $\to$ 94% post-balancing).*
2. **Which department is the problem, and which components inside it?**  
   *Assembly pod flags 104% Overload; BOM components `ASY-FRAME` and `ASY-MECH-INST` highlight backlogs.*
3. **Why? (Root cause with evidence & confidence)**  
   *Upstream starvation: Sensors department at 40% load chokes downstream assembly.*
4. **What should I do?**  
   *Loan 2 cross-trained operators from Fabrics to Sensors/Assembly.*
5. **Will it work?**  
   *CP-SAT feasibility verified; SimPy predicts throughput increase from 5.9 to 6.8 looms/day.*
6. **Where is loom #LM-100-0042 right now?**  
   *Live stage ribbon, hours-weighted progress, and blocking components list.*
7. **Who is working in each department this shift and the next?**  
   *Real-time roster, active shift headcounts, and skill coverage metrics.*
8. **Is the prediction model still reliable?**  
   *PSI drift metric calculated continuously; automated alert if PSI $\ge 0.10$.*

---

## 🏗️ 4. Architecture & Tech Stack

```
                     FRONTEND (Next.js 15 + R3F + TypeScript)
                           │  REST / WebSocket (Port 3000)
                        FastAPI (Port 8000)
         ┌─────────────────┼───────────────────┐
     Database          ML Services          Engines (Pure Python)
  PostgreSQL / SQLite   LightGBM / HW        Capacity · Load · Root Cause
  SQLAlchemy 2.x        Monitoring (PSI)     CP-SAT (OR-Tools) · SimPy Engine
```

- **Frontend**: Next.js 15 (App Router), React Three Fiber, Three.js, Lucide Icons, Pure CSS Tokens (Dark + Light Mode).
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn.
- **Optimization & ML**: Google OR-Tools CP-SAT, SimPy, LightGBM, Statsmodels, NumPy, Pandas, Scikit-learn.
- **Testing**: pytest (unit, property, ML leakage, capacity boundaries, scheduling).

---

## 📂 5. Repository Structure

```
HAL/
├── backend/
│   ├── app/
│   │   ├── api/routers/      # master, workforce, tracking, capacity
│   │   ├── capacity/         # Capacity engine, Monte-Carlo aggregation
│   │   ├── core/             # Config, shift utility, time math
│   │   ├── db/               # Session, Base, seed loaders
│   │   ├── ml/               # LightGBM build-time, Holt-Winters forecast, PSI monitoring
│   │   ├── models/           # SQLAlchemy 2.0 ORM models
│   │   ├── root_cause/       # Explanatory diagnosis engine
│   │   ├── scheduling/       # CP-SAT optimizer + independent feasibility checker
│   │   ├── simulation/       # SimPy event simulation engine & synthetic generator
│   │   ├── tracking/         # State machine, event projection, DAG readiness
│   │   ├── what_if/          # Before/After/Delta scenario evaluator
│   │   └── workforce/        # Roster, absence, skill-matching
│   └── tests/                # 28 comprehensive unit & integration tests
├── configs/
│   ├── catalog.yaml          # 5 Departments, 31 components, skills, DAG prerequisites
│   ├── factory.yaml          # Shifts, calendar, workstations, worker roster
│   └── synthetic/base.yaml   # Scenario generator distributions
├── frontend/
│   ├── src/app/
│   │   ├── components/       # Factory3D.tsx, DepartmentControlPanel.tsx
│   │   ├── globals.css       # Design tokens, Dark and Light mode styling
│   │   ├── layout.tsx
│   │   └── page.tsx          # Main digital twin dashboard
├── docs/                     # Full technical design documentation (01–07)
├── docker-compose.yml
├── Makefile
├── CLAUDE.md
└── README.md
```

---

## 🚀 6. Quickstart & Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Git

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
# Or run with poetry / conda environment
```

Initialize database & seed catalog:
```bash
python -m app.db.seed
```

Start FastAPI backend server:
```bash
uvicorn app.main:app --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Digital Twin UI will be live at: `http://localhost:3000`

---

## 🧪 7. Test Suite

Run the full backend test suite:
```bash
python -m pytest backend/tests -v
```

All 28 tests cover every project phase:
- `test_phase1.py`: Master endpoints & DAG acyclicity.
- `test_workforce.py`: Shift utility math, daily hour limits, roster coverage.
- `test_tracking.py`: Order unit generation, state machine transitions (409 on illegal).
- `test_simulation.py`: SimPy engine determinism & validation.
- `test_capacity.py`: Load boundary checks (69.9% / 70% / 95% / 95.1%), root cause, Monte-Carlo aggregation.
- `test_ml.py`: LightGBM quantile regression, leakage tests, Holt-Winters forecasting.
- `test_scheduling.py`: CP-SAT optimizer, feasibility checker, overlap detection, What-If engine.
- `test_monitoring.py`: PSI drift metrics, challenger evaluation, rollback safety.

---

## 🎨 8. User Interface Features

- **3D Factory Overview**: 5 interactive pods representing the factory floor with animated material transport chevrons between feeder departments and final assembly.
- **Department Drilldown**: Clicking any pod opens the Department Intelligence Panel with live 3D component rotating models, active BOM unit progress bars, and real-time operator allocations.
- **Theme Support**: Seamless Dark Mode and Light Mode switching with synced state and high-contrast accessibility.
- **Interactive Rebalancing**: Execute real-time worker transfer actions and run What-If simulations to resolve choke points.
- **Department Copilot**: Natural language assistant integrated into the control panel for contextual telemetry inquiries.

---

## 📜 9. License

MIT License. Developed for Advanced Powerloom Manufacturing Digital Twin Intelligence.
