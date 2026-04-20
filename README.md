# AE8803KHO — In-Space Assembly Mission Planner

Mission planning simulation tool for the on-orbit assembly of large modular spacecraft at the Earth-Sun L4 Lagrange point. Optimizes assembly campaigns using multi-objective dynamic programming with beam search, and compiles results into an AIAA-format PDF report or a standalone Markdown report.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12 | `py -3.12` on Windows |
| Node.js | 20+ | For the Next.js frontend |
| TinyTeX / TeX Live | 2025 | Required only for PDF report compilation |

---

## Quick Start

### 1 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2 — Install frontend dependencies

```bash
cd frontend
npm install
```

### 3 — Start the simulation server

Run from the **repo root**:

```bash
py -3.12 -m flask --app simulation.app run
```

The API listens on `http://127.0.0.1:5000`. Leave this terminal open.

### 4 — Start the frontend

In a **second terminal**, from the repo root:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## Using the Application

### Configuration Panel (left sidebar)

| Control | What it does |
|---------|-------------|
| **Spacecraft length** | Sets the overall scale; longer vehicles require more modules |
| **Propulsion** | Chemical / NTP / NEP / SEP — drives module mass and assembly hours |
| **Power system** | Solar / Fission / Fusion — gates which propulsion types are valid |
| **Cargo vehicles** | Select which launch vehicles are available for the campaign |
| **Crew vehicles** | Select which crewed vehicles can be used for crew rotations |
| **Transfer stages** | Select kick stages / tugs for LEO-only vehicles transiting to L4 |
| **Objective weights** | w₁ launches, w₂ time, w₃ cost — shift the optimizer's priorities |
| **EVA / IVA parameters** | Hours per session, pairs per IVA monitor, robotic penalty multiplier |
| **Proximity model** | α, β congestion parameters |

Click **Run Simulation** to execute the optimizer. Results appear in the dashboard.

### Objective Weight Effects

| Weight | Drives optimizer toward… | Vehicle choices |
|--------|--------------------------|----------------|
| **w₁ (launches)** | Fewer, larger flights; defers crew re-docking | Starship (150 t), SLS Block 2 (130 t) |
| **w₂ (time)** | Front-load cargo; launch crew at first airlock; prefer Hohmann over WSB (60 vs 120 day transit) | Fastest available vehicles |
| **w₃ (cost)** | Cheapest fleet; avoids SLS Block 2 ($4,100 M); prefers New Glenn ($90 M) and Crew Dragon ($220 M/mission); reuses fewer vehicle types to minimize first-flight premiums | Cost-per-kg efficient vehicles |

Equal weights (w₁ = w₂ = w₃ = 1) typically yield Falcon Heavy + Crew Dragon + NTP Tug.

> **Note on pad turnaround:** Each vehicle has a 2-period (14-day) minimum inter-launch interval. The beam-search secondary score blends pipeline depth with the weighted cost penalty, so the optimizer correctly waits for a cheaper vehicle to come off cooldown rather than filling the slot with an expensive one — even when the expensive vehicle is immediately eligible.

### Dashboard (main area)

- **Metrics summary** — total launches, mission duration, program cost, modules completed, cumulative proximity risk
- **Gantt chart** — one row per module showing WIP (purple) and completion (green); cargo/crew events shown as tick marks at the top
- **Resource utilization** — crew count and vehicle count over time on a dual axis
- **Cost breakdown** — two-panel horizontal bar chart: cargo vehicles (blue) and crew vehicles (orange), each bar = catalog price × flight count
- **Assembly progress** — cumulative modules completed over time vs. target

### Tagging runs for the report

After a simulation completes, click **Tag this run** in the metrics panel and give it a label. Tagged runs appear in the right sidebar. Tag multiple scenarios with different configurations to enable multi-scenario comparison and Pareto frontier visualization.

### Compiling reports

With at least one run tagged, the sidebar offers two report options:

#### PDF Report (requires TeX Live / MiKTeX)

Click **Compile Report**. The server will:
1. Generate matplotlib pgf charts for each tagged run
2. Run a 3×3×3 weight-combination sweep to populate the solution-space chart
3. Render the Jinja2 results template with your data
4. Run `pdflatex → bibtex → pdflatex → pdflatex`
5. Return the compiled AIAA-format PDF for download

> **Note:** PDF compilation requires TinyTeX or TeX Live with packages: `pgf`, `booktabs`, `siunitx`, `caption`, `microtype`, `lmodern`, `courier`, `rsfs`, `ragged2e`, `aiaa`. Install missing packages with `tlmgr install <package-name>`.

#### Markdown Report (no TeX required)

`POST /api/report/markdown` with the same tagged-runs payload returns a `report.md` file containing all scenario metrics, a launch timeline table, and a multi-scenario comparison table. No LaTeX installation needed.

---

## Vehicle Catalog

### Cargo Vehicles

| Vehicle | Nation | LEO (t) | Cost ($M) | Lead (mo) | Status |
|---------|--------|---------|-----------|-----------|--------|
| Starship | USA | 150 | 100 | 4.1 | Near-term |
| SLS Block 2 | USA | 130 | 4,100 | 6.0 | Operational |
| Falcon Heavy | USA | 64 | 150 | 0.9 | Operational |
| New Glenn | USA | 45 | 90 | 3.0 | Near-term |
| Vulcan Centaur | USA | 27 | 130 | 1.8 | Operational |
| Ariane 6 | Europe | 22 | 110 | 3.0 | Operational |
| KSLV-III | S. Korea | 10 | 80 | 18.0 | In development |
| GSLV Mk III | India | 10 | 50 | 3.0 | Operational |
| H3 | Japan | 7 | 50 | 3.0 | Operational |

### Crew Vehicles

| Vehicle | Nation | Crew | Cost ($M/mission) | Lead (mo) | Status |
|---------|--------|------|-------------------|-----------|--------|
| Crew Dragon | USA | 7 | 220 | 1.8 | Operational |
| Starliner | USA | 7 | 360 | 3.0 | Operational |
| Orion | USA/ESA | 4 | 600 | 6.0 | Operational |
| Starship HLS | USA | 6 | 250 | 6.0 | Near-term |

Costs reflect 2024–2025 pricing: SLS Block 2 from NASA OIG 2023; Crew Dragon and Starliner from NASA CCtCap per-seat pricing; Orion reflects capsule production cost per mission.

---

## Project Structure

```
AE8803KHO/
├── simulation/                    # Python backend
│   ├── app.py                     # Flask REST API (5 endpoints)
│   ├── report_builder.py          # Chart generation + pdflatex/markdown orchestration
│   ├── report_charts.py           # Matplotlib pgf chart functions
│   ├── solver/
│   │   ├── dp_solver.py           # Beam-search DP optimizer
│   │   └── objectives.py          # Multi-objective cost function
│   └── models/
│       ├── vehicles.py            # CargoVehicle, CrewVehicle, TransferStage
│       ├── modules.py             # Module catalog and assembly DAG
│       └── state.py               # Simulation state
├── data/                          # Vehicle and module JSON catalogs
├── frontend/                      # Next.js 16 web application
│   └── src/
│       ├── app/                   # App router pages and layout
│       ├── components/            # React components
│       ├── lib/                   # API client and TypeScript types
│       └── store/                 # Zustand state store
├── report/                        # LaTeX report
│   ├── report.tex                 # Master document
│   ├── aiaa.cls                   # AIAA conference class
│   ├── sections/                  # Static and Jinja2 template sections
│   │   ├── results.tex.j2         # LaTeX results template
│   │   └── results.md.j2          # Markdown results template
│   └── generated/                 # Auto-generated pgf charts (git-ignored)
└── tests/                         # Pytest test suite
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/catalog/cargo-vehicles` | Cargo vehicle catalog |
| `GET` | `/api/catalog/crew-vehicles` | Crew vehicle catalog |
| `GET` | `/api/catalog/transfer-stages` | Transfer stage catalog |
| `POST` | `/api/simulate` | Run the DP optimizer |
| `POST` | `/api/pareto` | Multi-weight Pareto sweep |
| `POST` | `/api/report` | Compile PDF report from tagged runs |
| `POST` | `/api/report/markdown` | Generate Markdown report from tagged runs |

---

## Running Tests

```bash
py -3.12 -m pytest tests/ -q
```
