# Mission Planning Simulation for In-Space Assembly of Large Structures

## Design Specification

**Course:** AE 8803 KHO — Space Logistics and Optimization (Prof. Koki Ho)
**Deadline:** April 20, 2026 (A section)
**Deliverables:** Final report (20 pages), programming code, 20-min video presentation

---

## 1. Overview

A simulation tool for planning the in-space assembly of a multi-kilometre-scale spacecraft at the Earth-Sun L4 Lagrange point. The system uses a dynamic programming (DP) approach over a time-expanded network to optimize launch scheduling, crew logistics, and on-orbit assembly sequencing. A web-based GUI provides interactive configuration, optimization, and real-time playback of the assembly campaign.

### Tech Stack
- **Simulation core:** Python (Flask API)
- **Frontend:** Next.js (React, Recharts/D3.js, HTML Canvas)
- **Data format:** JSON for vehicle catalogs, configs, and API communication

---

## 2. Problem Formulation & DP Structure

### Approach: Staged DP with Time-Expanded Network

Decision epochs are discretized into configurable time periods (default: 1 week). At each period, the optimizer decides which launches to send, what payloads to assign, and which assembly tasks to execute on-site.

### State Vector

At each epoch t:

```
S(t) = {
    modules_built:    bitmask of completed modules,
    crew_vehicles:    list of (vehicle_type, crew_onboard, time_remaining),
    cargo_in_transit: list of (payload, arrival_time),
    tugs_available:   count of reusable tugs back at LEO,
    resources_onsite: consumables remaining
}
```

### Decision Variables

```
D(t) = {
    launches:         list of (vehicle, payload_manifest),
    crew_allocation:  how many crew per vehicle, cargo trade-off,
    assembly_tasks:   which modules to work on this period,
    tug_assignments:  which tugs carry which payloads
}
```

### Bellman Equation

```
V(S, t) = min over D { cost(S, D, t) + V(S', t+1) }
```

### Multi-Objective Function

```
minimize: w1 * total_launches + w2 * total_time + w3 * total_cost
```

Where w1, w2, w3 are user-adjustable weights in the GUI.

---

## 3. Crew Model

### Crew Pool

All crew across all docked crew vehicles form a single shared pool at the assembly site. EVA pairs can be composed of crew members from different vehicles.

```
total_crew = sum(n_crew per docked crew vehicle)
```

### EVA Pair Constraint

EVAs require a minimum of 2 crew members working together (buddy system). A scaled IVA (intravehicular activity) support requirement means crew must remain inside to monitor EVA operations, operate robotic arms, manage comms, and handle emergencies.

```
n_iva_support = ceil(n_eva_pairs / max_pairs_per_iva)
n_eva_pairs = floor((total_crew - n_iva_support) / 2)
```

Where `max_pairs_per_iva` is configurable (default: 2).

| Crew on-site | IVA support | EVA pairs | Notes |
|---|---|---|---|
| 1-2 | — | 0 | Robotic-only work |
| 3 | 1 | 1 | Minimum EVA capability |
| 4 | 1 | 1 | 1 spare crew (rest/backup) |
| 5 | 1 | 2 | Max for 1 IVA monitor (at default 2:1) |
| 6 | 1 | 2 | 1 spare |
| 7 | 2 | 2 | Or 1 IVA monitoring 3 pairs if max_pairs_per_iva=3 |

### Crew Duty Constraints

- **EVA hours per session:** configurable (default: 6-8 hours)
- **One EVA session per pair per day**
- **Duty cycle:** fraction of time productive after rest/maintenance overhead (default: 60%)

```
crew_work = n_eva_pairs * max_eva_hours_per_session * eva_days_per_period
```

### Robotic Work

Robotic tasks proceed without crew and are not subject to EVA or duty cycle limits. Robots can operate 24/7 but with a configurable time penalty (default: 1.5x — a robotic task takes 1.5 times as long as the same task done by a crew EVA pair).

```
robotic_work = n_robotic_arms * hours_per_period * robotic_efficiency
```

### Crew Vehicle Persistence

Crew vehicles remain docked for the entire crew rotation duration, counting toward `n_vehicles_prox` the whole time. This creates a trade-off: crew speeds up assembly directly, but their vehicle adds to proximity congestion.

### Crew/Cargo Trade-off

Each crew vehicle has a total payload capacity. Unfilled crew seats can be traded for cargo mass:

```
available_cargo = total_payload_capacity - (n_crew_onboard * mass_per_crew)
```

Where `mass_per_crew` accounts for the person, seat, suit, and consumables for the mission duration.

---

## 4. Spacecraft Model & Module Decomposition

### Two Input Modes

**Parametric Mode:** User provides high-level specs (total length, diameter, structure type, subsystem complexity level) and the system auto-generates a module breakdown with assembly DAG.

**Catalog Mode:** User manually selects from the module library and defines quantities.

**Combined Mode:** Parametric generator outputs a catalog + DAG that the user can then customize.

### Module Catalog

#### Structural

| Module Type | Typical Mass (kg) | Assembly Type | Crew Required? | Notes |
|---|---|---|---|---|
| Truss Section | 5,000 | Robotic | No | ~200m backbone segment |
| Airlock/Docking Node | 5,000 | Crew | Yes | EVA access + berthing ports |

#### Habitation & Life Support

| Module Type | Typical Mass (kg) | Assembly Type | Crew Required? | Notes |
|---|---|---|---|---|
| Habitat Block | 20,000 | Crew | Yes | Pressurized module with integrated life support |

#### Power Systems

| Module Type | Typical Mass (kg) | Power Output (kW) | Assembly Type | Crew Required? | Notes |
|---|---|---|---|---|---|
| Solar Array Unit | 6,000 | ~100 | Robotic | No | Conventional, degrades with distance from Sun |
| Fission Reactor Unit | 15,000 | ~500 | Crew | Yes | Kilopower/KRUSTY-derived, compact, near-term |
| Fusion Reactor Unit | 40,000 | ~5,000+ | Crew | Yes | High output, enables large-scale NEP. Near-future |

#### Thermal

| Module Type | Typical Mass (kg) | Assembly Type | Crew Required? | Notes |
|---|---|---|---|---|
| Thermal System Unit | 3,000 | Robotic | No | Radiators + heat pipes bundled |

#### Propulsion

| Module Type | Typical Mass (kg) | Isp (s) | Thrust | Required Power System | Notes |
|---|---|---|---|---|---|
| Chemical (LOX/LH2) | 15,000 | ~450 | High | Any (minimal draw) | Proven, conventional |
| Nuclear Thermal (NTP) | 25,000 | ~900 | Medium-High | Any (self-contained reactor) | DRACO-derived, near-term |
| Nuclear Electric (NEP) | 30,000 | ~5,000+ | Low | Fission or Fusion | Draws from ship power grid |
| Solar Electric (SEP) | 10,000 | ~3,000 | Very Low | Solar Array | Power-limited by array capacity |

#### Communications & Avionics

| Module Type | Typical Mass (kg) | Assembly Type | Crew Required? | Notes |
|---|---|---|---|---|
| Avionics & Comms Suite | 4,000 | Crew | Yes | Flight computers + antennas + cabling |

#### Specialty

| Module Type | Typical Mass (kg) | Assembly Type | Crew Required? | Notes |
|---|---|---|---|---|
| Shielding Section | 4,000 | Robotic | No | Radiation/micrometeorite panels per truss section |
| Robotic Arm Station | 2,500 | Crew | Yes | Permanent manipulator for assembly & maintenance |

### Power-Propulsion Coupling Rules

- NEP requires sufficient Fission or Fusion reactor capacity installed before activation
- SEP requires sufficient Solar Array capacity installed before activation
- NTP and Chemical are self-contained (no power system dependency for propulsion)
- Fusion Reactor is a prerequisite for high-power NEP configurations and also feeds the general power grid

### Assembly Dependencies (DAG)

Each module has prerequisite modules forming a directed acyclic graph. The parametric generator creates appropriate dependencies automatically. Key ordering constraints:

- Truss sections must precede modules that mount to them
- Power systems must precede dependent propulsion systems
- At least one docking node before crew can board
- Some tasks can be parallelized, others are strictly sequential

### Scale

For a 2 km spacecraft, expect ~30-50 total modules. The parametric mode scales module counts linearly with spacecraft length.

---

## 5. Launch Vehicle Catalog & Transfer Model

### Cargo Launch Vehicles

| Vehicle | Nation | Payload to LEO (kg) | Fairing Volume (m³) | Cost per Launch ($M) | L4 Direct? | Status |
|---|---|---|---|---|---|---|
| Falcon Heavy (exp.) | USA | 63,800 | 145 | ~150 | No | Operational |
| SLS Block 2 | USA | 130,000 | 325 | ~2,000 | Yes | Operational |
| Starship | USA | 150,000 | ~1,000 | ~100 (target) | Yes | Near-term |
| Vulcan Centaur | USA | 27,200 | 95 | ~110 | No | Operational |
| New Glenn | USA | 45,000 | 160 | ~70 (est.) | No | Near-term |
| H3 | Japan (JAXA) | 6,500 | 40 | ~50 | No | Operational |
| Ariane 6 (A64) | Europe (ESA) | 21,600 | 180 | ~115 | No | Operational |
| KSLV-III | South Korea (KARI) | ~10,000 | TBD | TBD (est.) | No | In development |
| GSLV Mk III | India (ISRO) | 10,000 | 50 | ~50 | No | Operational |

Custom vehicles can also be defined by the user.

### Crew Vehicles

| Vehicle | Nation | Crew Capacity | Max Mission Duration | Mass (kg) | L4 Direct? |
|---|---|---|---|---|---|
| Crew Dragon | USA | 7 | ~180 days | 12,519 | No |
| Starliner | USA | 7 | ~210 days | 13,000 | No |
| Orion | USA/ESA | 4 | ~21 days | 26,520 | Yes |
| Starship HLS | USA | 4-6 | TBD | ~100,000 | Yes |

### Transfer Stages (Space Tugs)

LEO-only vehicles require a transfer stage to reach L4:

| Transfer Stage | Dry Mass (kg) | Propellant (kg) | Isp (s) | Reusable? |
|---|---|---|---|---|
| Chemical Kick Stage | 2,000 | 15,000 | 450 | No (expendable) |
| SEP Tug | 5,000 | 2,000 | 3,000 | Yes (returns to LEO) |
| NTP Tug | 8,000 | 10,000 | 900 | Yes (returns to LEO) |

Tug fleet sizing is a decision variable for the optimizer. Reusable tugs have a turnaround time for return to LEO and refueling.

### LEO to L4 Transfer Options

| Transfer Type | Delta-v (km/s) | Transfer Time (days) | Notes |
|---|---|---|---|
| Low-energy (WSB) | ~3.8 | ~120 | Fuel-efficient, slow |
| Direct (Hohmann-like) | ~4.1 | ~60 | Faster, more fuel |

Payload delivered to L4 computed via the rocket equation:

```
m_delivered = m_LEO * exp(-delta_v / (Isp * g0))
```

### Launch Scheduling Constraints

- Minimum interval between launches from the same provider (configurable pad turnaround)
- Maximum concurrent launches per period (global infrastructure limit)
- Crew comfort may restrict transfer type (crew prefers 60-day direct over 120-day low-energy)

---

## 6. Proximity Operations & Risk Model

### Scale-Adaptive Congestion Penalty

More simultaneous vehicles at the assembly site increase coordination overhead. The penalty scales inversely with build progress — early assembly has tighter quarters.

```
penalty(n, progress) = 1 + alpha * (n - 1)^beta / capacity(progress)
```

Where:

```
capacity(progress) = base_capacity + (max_capacity - base_capacity) * (S_built / S_total)
```

| Parameter | Default | Meaning |
|---|---|---|
| alpha | 0.1 | Congestion sensitivity coefficient |
| beta | 1.5 | Nonlinearity exponent (superlinear growth) |
| base_capacity | 2 | Early assembly — few vehicles fit without interfering |
| max_capacity | 10 | Fully built — a 2km structure has many independent work zones |

All parameters are user-adjustable in the GUI.

### What Counts as a Proximity Vehicle

- **Crew vehicles:** present for entire rotation duration
- **Cargo vehicles during unloading:** present for a configurable unloading period, then depart
- **Reusable tugs staging for return:** brief presence, still counts
- **Vehicles in final approach/departure:** counted during a configurable approach window

### Cumulative Collision Risk (Optional)

```
cumulative_risk = sum over all periods of: p_collision(n) * period_length
```

Displayed on the dashboard as a safety metric. Can optionally be added as a fourth objective weight.

### Optimizer Behavior

The penalty creates natural batching and phasing:
- Early phases: sequential, smaller deliveries; robotic-only phases attractive
- Mid phases: can overlap crew rotations and parallel cargo deliveries
- Late phases: can surge with many simultaneous vehicles
- Truss sections are naturally prioritized early to expand physical capacity

---

## 7. DP Solver & State Space Management

### State Space Explosion Mitigation

With ~30-50 modules, exact DP is intractable (2^30+ states). The solver uses a hybrid approach:

**Assembly DAG Phase Grouping:**
- Modules grouped into ~4-6 assembly phases based on the DAG structure:
  - Phase 1: Core truss sections (must come first, expands proximity capacity)
  - Phase 2: Power systems (enable dependent propulsion)
  - Phase 3: Habitation + propulsion (parallel paths)
  - Phase 4: Outfitting (shielding, comms, robotic arms)
- DP operates across phases (strategic: when to launch what, crew scheduling)
- Greedy/heuristic within phases (tactical: which specific module next given on-site availability)

**Forward DP with Beam Search Pruning:**
- Start from initial state, expand forward through time periods
- At each stage, keep only top-K states by objective value (K configurable, default ~1,000)
- Prune dominated states: if state A has more built, fewer launches, and less time than state B, discard B

### Performance Target

A typical 30-module spacecraft should solve in under 30 seconds on a standard laptop. A progress bar is fed to the frontend during solve.

### Solver Output

- Optimal (or near-optimal) campaign schedule
- Per-period decisions: launches, arrivals, assembly tasks, crew status
- Objective values for each weight combination
- Serialized to JSON for the frontend to consume and animate

---

## 8. Web GUI & Visualization (Next.js + Flask)

### Architecture

- **Backend:** Python simulation engine exposed via Flask REST API
- **Frontend:** Next.js app consuming the API
- **API endpoints:** run simulation, get results, list vehicle catalogs, parametric spacecraft generation

### GUI Layout

#### Configuration Panel (Input)

- Spacecraft definition: parametric sliders (length, type) or manual module catalog selection
- Launch vehicle selection: toggle available vehicles from catalog, define custom ones
- Crew vehicle selection with crew/cargo trade-off sliders
- Propulsion & power system choices with coupling validation
- Transfer stage / tug configuration
- DP parameters: period length, proximity penalty coefficients (alpha, beta, base/max capacity)
- Objective weight sliders: w1 (launches), w2 (time), w3 (cost)
- Run / reset buttons

#### Results Dashboard (Output)

- **Gantt chart:** Assembly timeline — launches, transit, arrivals, assembly tasks, crew rotations, color-coded by type
- **Resource utilization over time:** crew on-site, vehicles in proximity, modules completed (line/area charts)
- **Cost breakdown:** pie/bar charts by vehicle type, crew costs, tug operations
- **Pareto frontier plot:** trade-off surface when running multiple weight combinations
- **Proximity congestion over time:** penalty factor and vehicle count per period
- **Key metrics summary:** total launches, total time, total cost, peak crew, peak vehicles

#### 2D Assembly Progression View

- Top-down or side-view schematic of the spacecraft structure
- Modules color-coded by type (truss = gray, habitat = blue, power = yellow, propulsion = red, etc.)
- Docked vehicles shown at the assembly site, appearing/disappearing as they arrive/depart
- Current crew count and EVA pairs displayed as overlay

#### Real-Time Playback Controls

- **Play / Pause / Stop** buttons
- **Speed slider:** 1x, 2x, 5x, 10x (1x maps one simulation period to a few seconds of real time)
- **Timeline scrubber:** drag to jump to any point or let it advance during playback
- **Step forward/back:** advance one period at a time
- **All dashboard elements update in sync** during playback — Gantt highlights current period, charts show moving cursor, metrics accumulate live

### Tech Stack

- **Charts:** Recharts or D3.js
- **Gantt:** Custom D3 or lightweight Gantt library
- **2D assembly view:** HTML Canvas or SVG-based rendering
- **State management:** React context or Zustand
- **API communication:** REST with JSON payloads

---

## 9. Project Structure

```
AE8803KHO/
├── simulation/              # Python simulation core
│   ├── models/              # Module, vehicle, crew data models
│   ├── solver/              # DP solver, state management, pruning
│   ├── transfer/            # LEO→L4 transfer calculations
│   ├── proximity/           # Congestion penalty model
│   ├── parametric/          # Parametric spacecraft generator
│   └── app.py               # Flask API server
├── frontend/                # Next.js web GUI
│   ├── components/          # UI components (config panel, charts, 2D view)
│   └── pages/               # App pages
├── data/                    # Vehicle catalogs, default configs (JSON)
├── docs/                    # Design spec, report materials
└── README.md
```

### Key Dependencies

- **Python:** Flask, NumPy, dataclasses
- **Frontend:** Next.js, React, Recharts/D3.js, HTML Canvas

---

## 10. Deliverable Alignment

| Course Requirement | How This Project Delivers |
|---|---|
| Logistics techniques from class | Time-expanded network, DP optimization |
| Optimization/simulation | Multi-objective DP with beam search pruning |
| Final report (20 pages) | Motivation, approach (formulation), results (scenarios), discussion |
| 20-min video | Live demo: configure spacecraft → run optimizer → playback assembly animation |
| Visualization (strongly encouraged) | Gantt chart, resource dashboards, 2D assembly playback, Pareto frontier |
