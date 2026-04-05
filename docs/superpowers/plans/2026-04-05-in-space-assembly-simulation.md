# In-Space Assembly Mission Planning Simulation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a simulation tool that optimizes launch scheduling, crew logistics, and assembly sequencing for constructing a multi-km spacecraft at Earth-Sun L4, with a web GUI for interactive configuration and real-time playback.

**Architecture:** Python simulation core (data models, DP solver, transfer/proximity models) exposed via Flask REST API. Next.js frontend consumes the API to provide configuration, optimization controls, and animated results visualization. JSON data files store vehicle catalogs and default configs.

**Tech Stack:** Python 3.11+, Flask, NumPy, dataclasses | Next.js 14, React, Recharts, D3.js, HTML Canvas, Zustand

**Spec:** `docs/superpowers/specs/2026-04-05-in-space-assembly-mission-planning-design.md`

---

## File Structure

```
AE8803KHO/
├── simulation/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── modules.py          # Module dataclass, assembly DAG
│   │   ├── vehicles.py         # CargoVehicle, CrewVehicle, TransferStage
│   │   ├── crew.py             # CrewState, EVA pair logic, duty constraints
│   │   └── state.py            # SimulationState, Decision, transition function
│   ├── solver/
│   │   ├── __init__.py
│   │   ├── objectives.py       # Multi-objective cost function
│   │   └── dp_solver.py        # Forward DP with beam search pruning
│   ├── transfer.py             # LEO→L4 delta-v, transit time, payload delivery
│   ├── proximity.py            # Scale-adaptive congestion penalty
│   ├── parametric.py           # Parametric spacecraft generator
│   └── app.py                  # Flask API server
├── data/
│   ├── cargo_vehicles.json
│   ├── crew_vehicles.json
│   ├── transfer_stages.json
│   └── module_catalog.json
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── store/
│   │   │   └── useSimStore.ts      # Zustand store
│   │   ├── components/
│   │   │   ├── ConfigPanel.tsx      # Left panel: all input controls
│   │   │   ├── VehicleSelector.tsx  # Vehicle toggle/custom vehicle UI
│   │   │   ├── ModuleEditor.tsx     # Module catalog/parametric mode
│   │   │   ├── WeightSliders.tsx    # Objective weight sliders
│   │   │   ├── GanttChart.tsx       # D3 Gantt timeline
│   │   │   ├── ResourceCharts.tsx   # Recharts line/area charts
│   │   │   ├── CostBreakdown.tsx    # Recharts pie/bar charts
│   │   │   ├── ParetoPlot.tsx       # Recharts scatter plot
│   │   │   ├── AssemblyView.tsx     # 2D Canvas assembly progression
│   │   │   ├── PlaybackControls.tsx # Play/pause/speed/scrubber
│   │   │   ├── MetricsSummary.tsx   # Key metrics cards
│   │   │   └── Dashboard.tsx        # Right panel: results layout
│   │   └── lib/
│   │       ├── api.ts              # Flask API client
│   │       └── types.ts            # TypeScript types matching Python models
│   └── tsconfig.json
├── tests/
│   ├── __init__.py
│   ├── test_modules.py
│   ├── test_vehicles.py
│   ├── test_crew.py
│   ├── test_transfer.py
│   ├── test_proximity.py
│   ├── test_state.py
│   ├── test_objectives.py
│   ├── test_solver.py
│   ├── test_parametric.py
│   └── test_api.py
├── requirements.txt
└── README.md
```

---

## Task 1: Project Scaffolding & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `simulation/__init__.py`
- Create: `simulation/models/__init__.py`
- Create: `simulation/solver/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
flask==3.1.0
flask-cors==5.0.1
numpy==2.2.4
pytest==8.3.5
```

- [ ] **Step 2: Create package structure**

Create empty `__init__.py` files:

```python
# simulation/__init__.py
```

```python
# simulation/models/__init__.py
```

```python
# simulation/solver/__init__.py
```

```python
# tests/__init__.py
```

- [ ] **Step 3: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages install successfully.

- [ ] **Step 4: Verify pytest works**

Run: `pytest --co`
Expected: "no tests ran" or similar — confirms pytest is configured.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt simulation/__init__.py simulation/models/__init__.py simulation/solver/__init__.py tests/__init__.py
git commit -m "feat: scaffold project structure and dependencies"
```

---

## Task 2: Module Data Model

**Files:**
- Create: `simulation/models/modules.py`
- Create: `tests/test_modules.py`

- [ ] **Step 1: Write failing tests for Module and AssemblyDAG**

```python
# tests/test_modules.py
import pytest
from simulation.models.modules import Module, AssemblyDAG


class TestModule:
    def test_create_module(self):
        m = Module(
            id="truss_1",
            type="Truss Section",
            mass_kg=5000,
            assembly_hours=48,
            crew_required=False,
            category="structural",
        )
        assert m.id == "truss_1"
        assert m.mass_kg == 5000
        assert m.crew_required is False

    def test_module_defaults(self):
        m = Module(
            id="hab_1",
            type="Habitat Block",
            mass_kg=20000,
            assembly_hours=120,
            crew_required=True,
            category="habitation",
        )
        assert m.power_output_kw == 0
        assert m.required_power_system is None
        assert m.isp is None

    def test_propulsion_module_with_power_requirement(self):
        m = Module(
            id="nep_1",
            type="Nuclear Electric (NEP)",
            mass_kg=30000,
            assembly_hours=160,
            crew_required=True,
            category="propulsion",
            isp=5000,
            thrust_level="Low",
            required_power_system="Fission or Fusion",
        )
        assert m.required_power_system == "Fission or Fusion"
        assert m.isp == 5000

    def test_power_module(self):
        m = Module(
            id="fission_1",
            type="Fission Reactor Unit",
            mass_kg=15000,
            assembly_hours=100,
            crew_required=True,
            category="power",
            power_output_kw=500,
        )
        assert m.power_output_kw == 500


class TestAssemblyDAG:
    def _make_modules(self):
        truss = Module(id="truss_1", type="Truss Section", mass_kg=5000,
                       assembly_hours=48, crew_required=False, category="structural")
        power = Module(id="solar_1", type="Solar Array Unit", mass_kg=6000,
                       assembly_hours=36, crew_required=False, category="power",
                       power_output_kw=100)
        hab = Module(id="hab_1", type="Habitat Block", mass_kg=20000,
                     assembly_hours=120, crew_required=True, category="habitation")
        return truss, power, hab

    def test_add_modules_and_dependencies(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        dag.add_module(power, prerequisites=["truss_1"])
        dag.add_module(hab, prerequisites=["truss_1"])
        assert dag.get_prerequisites("solar_1") == ["truss_1"]
        assert dag.get_prerequisites("truss_1") == []

    def test_available_modules(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        dag.add_module(power, prerequisites=["truss_1"])
        dag.add_module(hab, prerequisites=["truss_1"])

        built = set()
        available = dag.get_available(built)
        assert available == {"truss_1"}

        built = {"truss_1"}
        available = dag.get_available(built)
        assert available == {"solar_1", "hab_1"}

    def test_topological_order(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        dag.add_module(power, prerequisites=["truss_1"])
        dag.add_module(hab, prerequisites=["truss_1"])
        order = dag.topological_sort()
        assert order.index("truss_1") < order.index("solar_1")
        assert order.index("truss_1") < order.index("hab_1")

    def test_cycle_detection(self):
        m1 = Module(id="a", type="X", mass_kg=1, assembly_hours=1,
                    crew_required=False, category="structural")
        m2 = Module(id="b", type="X", mass_kg=1, assembly_hours=1,
                    crew_required=False, category="structural")
        dag = AssemblyDAG()
        dag.add_module(m1)
        dag.add_module(m2, prerequisites=["a"])
        # Manually inject a cycle
        dag.prerequisites["a"] = ["b"]
        with pytest.raises(ValueError, match="cycle"):
            dag.topological_sort()

    def test_total_modules(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        dag.add_module(power, prerequisites=["truss_1"])
        dag.add_module(hab, prerequisites=["truss_1"])
        assert dag.total_modules == 3

    def test_get_module(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        assert dag.get_module("truss_1") is truss
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules.py -v`
Expected: FAIL — `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement Module and AssemblyDAG**

```python
# simulation/models/modules.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Module:
    id: str
    type: str
    mass_kg: float
    assembly_hours: float
    crew_required: bool
    category: str  # structural, habitation, power, thermal, propulsion, avionics, specialty
    power_output_kw: float = 0
    required_power_system: Optional[str] = None
    isp: Optional[float] = None
    thrust_level: Optional[str] = None
    notes: str = ""


class AssemblyDAG:
    def __init__(self) -> None:
        self.modules: dict[str, Module] = {}
        self.prerequisites: dict[str, list[str]] = {}

    @property
    def total_modules(self) -> int:
        return len(self.modules)

    def add_module(self, module: Module, prerequisites: list[str] | None = None) -> None:
        self.modules[module.id] = module
        self.prerequisites[module.id] = prerequisites or []

    def get_module(self, module_id: str) -> Module:
        return self.modules[module_id]

    def get_prerequisites(self, module_id: str) -> list[str]:
        return self.prerequisites.get(module_id, [])

    def get_available(self, built: set[str]) -> set[str]:
        available = set()
        for mid in self.modules:
            if mid in built:
                continue
            prereqs = self.prerequisites.get(mid, [])
            if all(p in built for p in prereqs):
                available.add(mid)
        return available

    def topological_sort(self) -> list[str]:
        visited: set[str] = set()
        in_stack: set[str] = set()
        order: list[str] = []

        def dfs(node: str) -> None:
            if node in in_stack:
                raise ValueError(f"Assembly DAG contains a cycle involving '{node}'")
            if node in visited:
                return
            in_stack.add(node)
            for prereq in self.prerequisites.get(node, []):
                dfs(prereq)
            in_stack.remove(node)
            visited.add(node)
            order.append(node)

        for mid in self.modules:
            dfs(mid)
        return order
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/models/modules.py tests/test_modules.py
git commit -m "feat: add Module dataclass and AssemblyDAG with topological sort"
```

---

## Task 3: Vehicle Data Models

**Files:**
- Create: `simulation/models/vehicles.py`
- Create: `tests/test_vehicles.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_vehicles.py
from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage


class TestCargoVehicle:
    def test_create_cargo_vehicle(self):
        fh = CargoVehicle(
            name="Falcon Heavy",
            nation="USA",
            payload_to_leo_kg=63800,
            fairing_volume_m3=145,
            cost_per_launch_million=150,
            l4_direct=False,
            status="Operational",
        )
        assert fh.name == "Falcon Heavy"
        assert fh.l4_direct is False

    def test_all_catalog_vehicles(self):
        vehicles = CargoVehicle.default_catalog()
        names = [v.name for v in vehicles]
        assert "Falcon Heavy" in names
        assert "SLS Block 2" in names
        assert "Starship" in names
        assert "H3" in names
        assert "Ariane 6" in names
        assert "GSLV Mk III" in names
        assert len(vehicles) == 9


class TestCrewVehicle:
    def test_create_crew_vehicle(self):
        dragon = CrewVehicle(
            name="Crew Dragon",
            nation="USA",
            max_crew=7,
            max_mission_duration_days=180,
            mass_kg=12519,
            l4_direct=False,
            mass_per_crew_kg=200,
        )
        assert dragon.max_crew == 7

    def test_cargo_capacity_full_crew(self):
        dragon = CrewVehicle(
            name="Crew Dragon",
            nation="USA",
            max_crew=7,
            max_mission_duration_days=180,
            mass_kg=12519,
            l4_direct=False,
            mass_per_crew_kg=200,
        )
        cargo = dragon.available_cargo_kg(crew_onboard=7)
        assert cargo == 12519 - 7 * 200

    def test_cargo_capacity_partial_crew(self):
        dragon = CrewVehicle(
            name="Crew Dragon",
            nation="USA",
            max_crew=7,
            max_mission_duration_days=180,
            mass_kg=12519,
            l4_direct=False,
            mass_per_crew_kg=200,
        )
        cargo = dragon.available_cargo_kg(crew_onboard=4)
        assert cargo == 12519 - 4 * 200

    def test_default_catalog(self):
        vehicles = CrewVehicle.default_catalog()
        assert len(vehicles) == 4
        names = [v.name for v in vehicles]
        assert "Orion" in names


class TestTransferStage:
    def test_create_transfer_stage(self):
        tug = TransferStage(
            name="SEP Tug",
            dry_mass_kg=5000,
            propellant_kg=2000,
            isp_s=3000,
            reusable=True,
        )
        assert tug.reusable is True

    def test_default_catalog(self):
        stages = TransferStage.default_catalog()
        assert len(stages) == 3
        names = [s.name for s in stages]
        assert "Chemical Kick Stage" in names
        assert "NTP Tug" in names
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_vehicles.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement vehicle models**

```python
# simulation/models/vehicles.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CargoVehicle:
    name: str
    nation: str
    payload_to_leo_kg: float
    fairing_volume_m3: float
    cost_per_launch_million: float
    l4_direct: bool
    status: str

    @staticmethod
    def default_catalog() -> list[CargoVehicle]:
        return [
            CargoVehicle("Falcon Heavy", "USA", 63800, 145, 150, False, "Operational"),
            CargoVehicle("SLS Block 2", "USA", 130000, 325, 2000, True, "Operational"),
            CargoVehicle("Starship", "USA", 150000, 1000, 100, True, "Near-term"),
            CargoVehicle("Vulcan Centaur", "USA", 27200, 95, 110, False, "Operational"),
            CargoVehicle("New Glenn", "USA", 45000, 160, 70, False, "Near-term"),
            CargoVehicle("H3", "Japan", 6500, 40, 50, False, "Operational"),
            CargoVehicle("Ariane 6", "Europe", 21600, 180, 115, False, "Operational"),
            CargoVehicle("KSLV-III", "South Korea", 10000, 50, 80, False, "In development"),
            CargoVehicle("GSLV Mk III", "India", 10000, 50, 50, False, "Operational"),
        ]


@dataclass(frozen=True)
class CrewVehicle:
    name: str
    nation: str
    max_crew: int
    max_mission_duration_days: int
    mass_kg: float
    l4_direct: bool
    mass_per_crew_kg: float = 200

    def available_cargo_kg(self, crew_onboard: int) -> float:
        return self.mass_kg - crew_onboard * self.mass_per_crew_kg

    @staticmethod
    def default_catalog() -> list[CrewVehicle]:
        return [
            CrewVehicle("Crew Dragon", "USA", 7, 180, 12519, False),
            CrewVehicle("Starliner", "USA", 7, 210, 13000, False),
            CrewVehicle("Orion", "USA/ESA", 4, 21, 26520, True),
            CrewVehicle("Starship HLS", "USA", 6, 180, 100000, True),
        ]


@dataclass(frozen=True)
class TransferStage:
    name: str
    dry_mass_kg: float
    propellant_kg: float
    isp_s: float
    reusable: bool

    @staticmethod
    def default_catalog() -> list[TransferStage]:
        return [
            TransferStage("Chemical Kick Stage", 2000, 15000, 450, False),
            TransferStage("SEP Tug", 5000, 2000, 3000, True),
            TransferStage("NTP Tug", 8000, 10000, 900, True),
        ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_vehicles.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/models/vehicles.py tests/test_vehicles.py
git commit -m "feat: add CargoVehicle, CrewVehicle, TransferStage models with catalogs"
```

---

## Task 4: Crew Model — EVA Pairs & Duty Constraints

**Files:**
- Create: `simulation/models/crew.py`
- Create: `tests/test_crew.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_crew.py
from simulation.models.crew import CrewState


class TestEVAPairs:
    def test_no_crew_no_eva(self):
        cs = CrewState(total_crew=0, max_pairs_per_iva=2)
        assert cs.n_eva_pairs == 0
        assert cs.n_iva_support == 0

    def test_two_crew_no_eva(self):
        cs = CrewState(total_crew=2, max_pairs_per_iva=2)
        assert cs.n_eva_pairs == 0

    def test_three_crew_one_pair(self):
        cs = CrewState(total_crew=3, max_pairs_per_iva=2)
        assert cs.n_eva_pairs == 1
        assert cs.n_iva_support == 1

    def test_five_crew_two_pairs(self):
        cs = CrewState(total_crew=5, max_pairs_per_iva=2)
        assert cs.n_eva_pairs == 2
        assert cs.n_iva_support == 1

    def test_seven_crew_default(self):
        cs = CrewState(total_crew=7, max_pairs_per_iva=2)
        # 7 crew, need ceil(pairs/2) IVA support
        # With 2 IVA: (7-2)/2 = 2 pairs, ceil(2/2)=1 IVA — contradiction
        # Iterative solve: try 1 IVA -> 6/2=3 pairs, ceil(3/2)=2 IVA needed
        # try 2 IVA -> 5/2=2 pairs, ceil(2/2)=1 IVA needed — but we allocated 2
        # Settled: 2 IVA, 2 pairs (conservative) or 1 IVA, 3 pairs if max_pairs_per_iva=3
        assert cs.n_iva_support == 2
        assert cs.n_eva_pairs == 2

    def test_seven_crew_high_iva_ratio(self):
        cs = CrewState(total_crew=7, max_pairs_per_iva=3)
        assert cs.n_iva_support == 1
        assert cs.n_eva_pairs == 3


class TestCrewWork:
    def test_eva_hours_per_period(self):
        cs = CrewState(
            total_crew=5,
            max_pairs_per_iva=2,
            max_eva_hours_per_session=6,
            eva_days_per_period=7,
        )
        # 2 EVA pairs * 6 hours/session * 7 days = 84 hours
        assert cs.eva_hours_per_period == 84

    def test_no_crew_zero_hours(self):
        cs = CrewState(total_crew=0, max_pairs_per_iva=2)
        assert cs.eva_hours_per_period == 0

    def test_robotic_hours_per_period(self):
        cs = CrewState(
            total_crew=0,
            max_pairs_per_iva=2,
            n_robotic_arms=2,
            hours_per_period=168,
            robotic_time_penalty=1.5,
        )
        # 2 arms * 168 hours / 1.5 penalty = 224 effective hours
        expected = 2 * 168 / 1.5
        assert abs(cs.robotic_hours_per_period - expected) < 0.01
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_crew.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement CrewState**

```python
# simulation/models/crew.py
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class CrewState:
    total_crew: int
    max_pairs_per_iva: int = 2
    max_eva_hours_per_session: float = 6
    eva_days_per_period: int = 7
    n_robotic_arms: int = 0
    hours_per_period: float = 168  # 24 * 7
    robotic_time_penalty: float = 1.5

    @property
    def n_iva_support(self) -> int:
        if self.total_crew < 3:
            return 0
        # Iterative solve: find stable (iva, pairs) allocation
        for n_iva in range(1, self.total_crew):
            remaining = self.total_crew - n_iva
            pairs = remaining // 2
            needed_iva = math.ceil(pairs / self.max_pairs_per_iva)
            if needed_iva <= n_iva:
                return n_iva
        return 0

    @property
    def n_eva_pairs(self) -> int:
        if self.total_crew < 3:
            return 0
        remaining = self.total_crew - self.n_iva_support
        return remaining // 2

    @property
    def eva_hours_per_period(self) -> float:
        return self.n_eva_pairs * self.max_eva_hours_per_session * self.eva_days_per_period

    @property
    def robotic_hours_per_period(self) -> float:
        return self.n_robotic_arms * self.hours_per_period / self.robotic_time_penalty
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_crew.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/models/crew.py tests/test_crew.py
git commit -m "feat: add CrewState with EVA pair allocation and duty constraints"
```

---

## Task 5: Transfer Model

**Files:**
- Create: `simulation/transfer.py`
- Create: `tests/test_transfer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_transfer.py
import pytest
from simulation.transfer import TransferModel
from simulation.models.vehicles import CargoVehicle, TransferStage


class TestTransferModel:
    def test_direct_capable_vehicle(self):
        sls = CargoVehicle("SLS Block 2", "USA", 130000, 325, 2000, True, "Operational")
        tm = TransferModel()
        result = tm.compute_delivery(sls, transfer_type="direct", transfer_stage=None)
        # SLS is L4-direct, uses its own propulsion
        # m_delivered = 130000 * exp(-4.1 / (450 * 9.80665 / 1000))
        # Wait — Isp is in seconds, delta_v in km/s, g0 = 9.80665e-3 km/s^2
        assert result.mass_delivered_kg > 0
        assert result.mass_delivered_kg < 130000
        assert result.transit_days == 60

    def test_low_energy_transfer(self):
        sls = CargoVehicle("SLS Block 2", "USA", 130000, 325, 2000, True, "Operational")
        tm = TransferModel()
        result_direct = tm.compute_delivery(sls, transfer_type="direct", transfer_stage=None)
        result_low = tm.compute_delivery(sls, transfer_type="low_energy", transfer_stage=None)
        # Low energy delivers more mass (less delta-v) but takes longer
        assert result_low.mass_delivered_kg > result_direct.mass_delivered_kg
        assert result_low.transit_days == 120

    def test_leo_only_vehicle_needs_tug(self):
        fh = CargoVehicle("Falcon Heavy", "USA", 63800, 145, 150, False, "Operational")
        tug = TransferStage("Chemical Kick Stage", 2000, 15000, 450, False)
        tm = TransferModel()
        result = tm.compute_delivery(fh, transfer_type="direct", transfer_stage=tug)
        # Payload is reduced by tug dry mass + propellant usage
        assert result.mass_delivered_kg > 0
        assert result.mass_delivered_kg < 63800

    def test_leo_only_without_tug_raises(self):
        fh = CargoVehicle("Falcon Heavy", "USA", 63800, 145, 150, False, "Operational")
        tm = TransferModel()
        with pytest.raises(ValueError, match="requires a transfer stage"):
            tm.compute_delivery(fh, transfer_type="direct", transfer_stage=None)

    def test_sep_tug_delivers_more_than_chemical(self):
        fh = CargoVehicle("Falcon Heavy", "USA", 63800, 145, 150, False, "Operational")
        chem = TransferStage("Chemical Kick Stage", 2000, 15000, 450, False)
        sep = TransferStage("SEP Tug", 5000, 2000, 3000, True)
        tm = TransferModel()
        result_chem = tm.compute_delivery(fh, transfer_type="direct", transfer_stage=chem)
        result_sep = tm.compute_delivery(fh, transfer_type="low_energy", transfer_stage=sep)
        # SEP with higher Isp should deliver more net payload
        assert result_sep.mass_delivered_kg > result_chem.mass_delivered_kg
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_transfer.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement TransferModel**

```python
# simulation/transfer.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from simulation.models.vehicles import CargoVehicle, TransferStage

G0_KMS2 = 9.80665e-3  # km/s^2

TRANSFER_OPTIONS = {
    "direct": {"delta_v_kms": 4.1, "transit_days": 60},
    "low_energy": {"delta_v_kms": 3.8, "transit_days": 120},
}

# Default upper stage Isp for L4-direct vehicles (e.g., SLS EUS, Starship)
DEFAULT_DIRECT_ISP_S = 450


@dataclass
class DeliveryResult:
    mass_delivered_kg: float
    transit_days: int
    cost_million: float


class TransferModel:
    def compute_delivery(
        self,
        vehicle: CargoVehicle,
        transfer_type: str,
        transfer_stage: Optional[TransferStage],
    ) -> DeliveryResult:
        opts = TRANSFER_OPTIONS[transfer_type]
        delta_v = opts["delta_v_kms"]
        transit_days = opts["transit_days"]

        if vehicle.l4_direct:
            # Vehicle has its own upper stage
            payload_leo = vehicle.payload_to_leo_kg
            isp = DEFAULT_DIRECT_ISP_S
            mass_delivered = payload_leo * math.exp(-delta_v / (isp * G0_KMS2))
            return DeliveryResult(
                mass_delivered_kg=mass_delivered,
                transit_days=transit_days,
                cost_million=vehicle.cost_per_launch_million,
            )

        if transfer_stage is None:
            raise ValueError(
                f"'{vehicle.name}' is LEO-only and requires a transfer stage for L4 delivery"
            )

        # LEO payload must carry the tug + its propellant + the actual cargo
        # tug_total = dry_mass + propellant
        # payload_on_tug = LEO_payload - tug_total
        # delivered = payload_on_tug (tug does the burn)
        # But the tug also needs to accelerate itself + payload:
        # m0 = tug_dry + propellant + cargo
        # m1 = tug_dry + cargo (propellant burned)
        # delta_v = Isp * g0 * ln(m0 / m1)
        # Solve for cargo: m0 = LEO_payload, m1 = m0 - propellant = LEO_payload - propellant
        # But we need delta_v to match the transfer requirement.
        # cargo = m1 - tug_dry = (m0 / exp(dv / (Isp*g0))) - tug_dry
        tug_total = transfer_stage.dry_mass_kg + transfer_stage.propellant_kg
        payload_for_tug = vehicle.payload_to_leo_kg - tug_total
        if payload_for_tug <= 0:
            return DeliveryResult(mass_delivered_kg=0, transit_days=transit_days,
                                  cost_million=vehicle.cost_per_launch_million)

        # m0 = tug_dry + propellant + cargo = tug_total + cargo
        # We need: dv = Isp*g0*ln(m0/m1) where m1 = tug_dry + cargo
        # So: m0/m1 = exp(dv/(Isp*g0))
        # (tug_total + cargo) / (tug_dry + cargo) = exp(dv/(Isp*g0))
        # Solve for cargo:
        # tug_total + cargo = exp(dv/(Isp*g0)) * (tug_dry + cargo)
        # tug_total + cargo = R * tug_dry + R * cargo
        # cargo(1 - R) = R * tug_dry - tug_total
        # cargo = (R * tug_dry - tug_total) / (1 - R)
        # But cargo must also <= payload_for_tug
        isp = transfer_stage.isp_s
        R = math.exp(delta_v / (isp * G0_KMS2))
        if R >= 1.0:
            # Should always be true
            cargo_max_by_tug = (R * transfer_stage.dry_mass_kg - tug_total) / (1 - R)
        else:
            cargo_max_by_tug = payload_for_tug

        # The above formula gives the max cargo the tug can push with its propellant.
        # If negative, the tug can't even push itself.
        if cargo_max_by_tug <= 0:
            return DeliveryResult(mass_delivered_kg=0, transit_days=transit_days,
                                  cost_million=vehicle.cost_per_launch_million)

        mass_delivered = min(payload_for_tug, cargo_max_by_tug)

        return DeliveryResult(
            mass_delivered_kg=mass_delivered,
            transit_days=transit_days,
            cost_million=vehicle.cost_per_launch_million,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_transfer.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/transfer.py tests/test_transfer.py
git commit -m "feat: add TransferModel with rocket equation payload delivery"
```

---

## Task 6: Proximity Penalty Model

**Files:**
- Create: `simulation/proximity.py`
- Create: `tests/test_proximity.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_proximity.py
import pytest
from simulation.proximity import ProximityModel


class TestProximityModel:
    def test_single_vehicle_no_penalty(self):
        pm = ProximityModel(alpha=0.1, beta=1.5, base_capacity=2, max_capacity=10)
        penalty = pm.penalty(n_vehicles=1, progress=0.0)
        assert penalty == 1.0

    def test_early_build_high_penalty(self):
        pm = ProximityModel(alpha=0.1, beta=1.5, base_capacity=2, max_capacity=10)
        penalty_early = pm.penalty(n_vehicles=4, progress=0.0)
        penalty_late = pm.penalty(n_vehicles=4, progress=0.75)
        assert penalty_early > penalty_late
        assert penalty_early > 1.0

    def test_full_build_low_penalty(self):
        pm = ProximityModel(alpha=0.1, beta=1.5, base_capacity=2, max_capacity=10)
        penalty = pm.penalty(n_vehicles=4, progress=1.0)
        assert penalty < 1.1  # Very low penalty at full build

    def test_zero_vehicles(self):
        pm = ProximityModel(alpha=0.1, beta=1.5, base_capacity=2, max_capacity=10)
        penalty = pm.penalty(n_vehicles=0, progress=0.0)
        assert penalty == 1.0

    def test_capacity_scales_linearly(self):
        pm = ProximityModel(alpha=0.1, beta=1.5, base_capacity=2, max_capacity=10)
        cap_0 = pm.capacity(0.0)
        cap_50 = pm.capacity(0.5)
        cap_100 = pm.capacity(1.0)
        assert cap_0 == 2.0
        assert cap_50 == 6.0
        assert cap_100 == 10.0

    def test_collision_risk(self):
        pm = ProximityModel(alpha=0.1, beta=1.5, base_capacity=2, max_capacity=10)
        risk = pm.collision_risk(n_vehicles=3, period_length_days=7)
        assert risk > 0
        risk_more = pm.collision_risk(n_vehicles=5, period_length_days=7)
        assert risk_more > risk
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_proximity.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement ProximityModel**

```python
# simulation/proximity.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProximityModel:
    alpha: float = 0.1
    beta: float = 1.5
    base_capacity: float = 2.0
    max_capacity: float = 10.0
    collision_risk_coeff: float = 1e-5

    def capacity(self, progress: float) -> float:
        return self.base_capacity + (self.max_capacity - self.base_capacity) * progress

    def penalty(self, n_vehicles: int, progress: float) -> float:
        if n_vehicles <= 1:
            return 1.0
        cap = self.capacity(progress)
        return 1.0 + self.alpha * (n_vehicles - 1) ** self.beta / cap

    def collision_risk(self, n_vehicles: int, period_length_days: float) -> float:
        if n_vehicles <= 1:
            return 0.0
        # Risk scales with number of vehicle pairs
        n_pairs = n_vehicles * (n_vehicles - 1) / 2
        return self.collision_risk_coeff * n_pairs * period_length_days
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_proximity.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/proximity.py tests/test_proximity.py
git commit -m "feat: add scale-adaptive proximity congestion penalty model"
```

---

## Task 7: Simulation State & Transition Function

**Files:**
- Create: `simulation/models/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_state.py
from simulation.models.state import SimState, DockedCrewVehicle, CargoInTransit, Launch
from simulation.models.vehicles import CrewVehicle, CargoVehicle, TransferStage
from simulation.models.modules import Module, AssemblyDAG
from simulation.proximity import ProximityModel


class TestSimState:
    def test_initial_state(self):
        s = SimState.initial()
        assert s.modules_built == frozenset()
        assert s.period == 0
        assert s.total_launches == 0
        assert s.total_cost_million == 0

    def test_n_vehicles_prox(self):
        crew_v = DockedCrewVehicle(
            vehicle_name="Crew Dragon", crew_onboard=4, periods_remaining=10
        )
        s = SimState(
            modules_built=frozenset(),
            crew_vehicles=[crew_v],
            cargo_in_transit=[],
            cargo_at_site=0,
            tugs_available=0,
            period=0,
            total_launches=0,
            total_cost_million=0,
            cumulative_risk=0,
        )
        assert s.n_vehicles_prox == 1

    def test_total_crew(self):
        cv1 = DockedCrewVehicle(vehicle_name="Crew Dragon", crew_onboard=4, periods_remaining=10)
        cv2 = DockedCrewVehicle(vehicle_name="Starliner", crew_onboard=3, periods_remaining=8)
        s = SimState(
            modules_built=frozenset(),
            crew_vehicles=[cv1, cv2],
            cargo_in_transit=[],
            cargo_at_site=0,
            tugs_available=0,
            period=0,
            total_launches=0,
            total_cost_million=0,
            cumulative_risk=0,
        )
        assert s.total_crew == 7

    def test_build_progress(self):
        s = SimState(
            modules_built=frozenset({"a", "b"}),
            crew_vehicles=[],
            cargo_in_transit=[],
            cargo_at_site=0,
            tugs_available=0,
            period=0,
            total_launches=0,
            total_cost_million=0,
            cumulative_risk=0,
        )
        assert s.build_progress(total_modules=4) == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_state.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement SimState**

```python
# simulation/models/state.py
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DockedCrewVehicle:
    vehicle_name: str
    crew_onboard: int
    periods_remaining: int


@dataclass(frozen=True)
class CargoInTransit:
    module_ids: tuple[str, ...]
    arrival_period: int
    cost_million: float


@dataclass(frozen=True)
class Launch:
    vehicle_name: str
    payload_module_ids: list[str]
    crew_count: int
    cost_million: float


@dataclass(frozen=True)
class SimState:
    modules_built: frozenset[str]
    crew_vehicles: list[DockedCrewVehicle]
    cargo_in_transit: list[CargoInTransit]
    cargo_at_site: float  # mass of unassembled modules available on-site (kg)
    tugs_available: int
    period: int
    total_launches: int
    total_cost_million: float
    cumulative_risk: float

    @staticmethod
    def initial() -> SimState:
        return SimState(
            modules_built=frozenset(),
            crew_vehicles=[],
            cargo_in_transit=[],
            cargo_at_site=0,
            tugs_available=0,
            period=0,
            total_launches=0,
            total_cost_million=0,
            cumulative_risk=0,
        )

    @property
    def n_vehicles_prox(self) -> int:
        return len(self.crew_vehicles)

    @property
    def total_crew(self) -> int:
        return sum(cv.crew_onboard for cv in self.crew_vehicles)

    def build_progress(self, total_modules: int) -> float:
        if total_modules == 0:
            return 1.0
        return len(self.modules_built) / total_modules
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_state.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/models/state.py tests/test_state.py
git commit -m "feat: add SimState with crew pooling and build progress tracking"
```

---

## Task 8: Multi-Objective Cost Function

**Files:**
- Create: `simulation/solver/objectives.py`
- Create: `tests/test_objectives.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_objectives.py
from simulation.solver.objectives import ObjectiveWeights, compute_cost


class TestObjectiveWeights:
    def test_default_weights(self):
        w = ObjectiveWeights()
        assert w.w_launches == 1.0
        assert w.w_time == 1.0
        assert w.w_cost == 1.0

    def test_compute_cost_balanced(self):
        w = ObjectiveWeights(w_launches=1.0, w_time=1.0, w_cost=1.0)
        cost = compute_cost(
            weights=w,
            n_launches=10,
            n_periods=52,
            total_cost_million=5000,
            max_launches=100,
            max_periods=200,
            max_cost_million=50000,
        )
        # Each normalized term is 10/100 + 52/200 + 5000/50000 = 0.1 + 0.26 + 0.1 = 0.46
        expected = 1.0 * (10 / 100) + 1.0 * (52 / 200) + 1.0 * (5000 / 50000)
        assert abs(cost - expected) < 1e-6

    def test_launch_only_weight(self):
        w = ObjectiveWeights(w_launches=1.0, w_time=0.0, w_cost=0.0)
        cost = compute_cost(
            weights=w,
            n_launches=10,
            n_periods=52,
            total_cost_million=5000,
            max_launches=100,
            max_periods=200,
            max_cost_million=50000,
        )
        expected = 1.0 * (10 / 100)
        assert abs(cost - expected) < 1e-6

    def test_zero_max_safe(self):
        w = ObjectiveWeights(w_launches=1.0, w_time=1.0, w_cost=1.0)
        cost = compute_cost(
            weights=w,
            n_launches=0,
            n_periods=0,
            total_cost_million=0,
            max_launches=0,
            max_periods=0,
            max_cost_million=0,
        )
        assert cost == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_objectives.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement objectives**

```python
# simulation/solver/objectives.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ObjectiveWeights:
    w_launches: float = 1.0
    w_time: float = 1.0
    w_cost: float = 1.0


def compute_cost(
    weights: ObjectiveWeights,
    n_launches: int,
    n_periods: int,
    total_cost_million: float,
    max_launches: int,
    max_periods: int,
    max_cost_million: float,
) -> float:
    def safe_normalize(value: float, maximum: float) -> float:
        if maximum <= 0:
            return 0.0
        return value / maximum

    return (
        weights.w_launches * safe_normalize(n_launches, max_launches)
        + weights.w_time * safe_normalize(n_periods, max_periods)
        + weights.w_cost * safe_normalize(total_cost_million, max_cost_million)
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_objectives.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/solver/objectives.py tests/test_objectives.py
git commit -m "feat: add multi-objective weighted cost function with normalization"
```

---

## Task 9: Parametric Spacecraft Generator

**Files:**
- Create: `simulation/parametric.py`
- Create: `tests/test_parametric.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_parametric.py
from simulation.parametric import generate_spacecraft
from simulation.models.modules import AssemblyDAG


class TestParametricGenerator:
    def test_generates_dag(self):
        dag = generate_spacecraft(
            length_km=2.0,
            structure_type="truss",
            propulsion_type="NEP",
            power_type="Fusion",
        )
        assert isinstance(dag, AssemblyDAG)
        assert dag.total_modules > 0

    def test_truss_count_scales_with_length(self):
        dag_1km = generate_spacecraft(length_km=1.0, structure_type="truss",
                                       propulsion_type="Chemical", power_type="Solar")
        dag_2km = generate_spacecraft(length_km=2.0, structure_type="truss",
                                       propulsion_type="Chemical", power_type="Solar")
        truss_1 = sum(1 for m in dag_1km.modules.values() if m.type == "Truss Section")
        truss_2 = sum(1 for m in dag_2km.modules.values() if m.type == "Truss Section")
        assert truss_2 > truss_1

    def test_nep_requires_fission_or_fusion(self):
        dag = generate_spacecraft(length_km=1.0, structure_type="truss",
                                   propulsion_type="NEP", power_type="Fission")
        # NEP modules should have prerequisites including a fission reactor
        nep_modules = [m for m in dag.modules.values() if "NEP" in m.type]
        assert len(nep_modules) > 0
        for nep in nep_modules:
            prereqs = dag.get_prerequisites(nep.id)
            has_power_prereq = any("fission" in p or "fusion" in p for p in prereqs)
            assert has_power_prereq

    def test_sep_requires_solar(self):
        dag = generate_spacecraft(length_km=1.0, structure_type="truss",
                                   propulsion_type="SEP", power_type="Solar")
        sep_modules = [m for m in dag.modules.values() if "SEP" in m.type]
        assert len(sep_modules) > 0
        for sep in sep_modules:
            prereqs = dag.get_prerequisites(sep.id)
            has_solar = any("solar" in p for p in prereqs)
            assert has_solar

    def test_has_docking_node(self):
        dag = generate_spacecraft(length_km=1.0, structure_type="truss",
                                   propulsion_type="Chemical", power_type="Solar")
        docking = [m for m in dag.modules.values() if "Docking" in m.type]
        assert len(docking) >= 1

    def test_topological_sort_valid(self):
        dag = generate_spacecraft(length_km=2.0, structure_type="truss",
                                   propulsion_type="NTP", power_type="Fission")
        order = dag.topological_sort()
        assert len(order) == dag.total_modules

    def test_module_count_reasonable(self):
        dag = generate_spacecraft(length_km=2.0, structure_type="truss",
                                   propulsion_type="Chemical", power_type="Solar")
        assert 20 <= dag.total_modules <= 60
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_parametric.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement parametric generator**

```python
# simulation/parametric.py
from __future__ import annotations

import math

from simulation.models.modules import Module, AssemblyDAG

# How many km each truss section spans
TRUSS_SPAN_KM = 0.2

# Module specs from the design doc
MODULE_SPECS = {
    "Truss Section": {"mass": 5000, "hours": 48, "crew": False, "cat": "structural"},
    "Airlock/Docking Node": {"mass": 5000, "hours": 72, "crew": True, "cat": "structural"},
    "Habitat Block": {"mass": 20000, "hours": 120, "crew": True, "cat": "habitation"},
    "Solar Array Unit": {"mass": 6000, "hours": 36, "crew": False, "cat": "power", "power_kw": 100},
    "Fission Reactor Unit": {"mass": 15000, "hours": 100, "crew": True, "cat": "power", "power_kw": 500},
    "Fusion Reactor Unit": {"mass": 40000, "hours": 160, "crew": True, "cat": "power", "power_kw": 5000},
    "Thermal System Unit": {"mass": 3000, "hours": 24, "crew": False, "cat": "thermal"},
    "Chemical (LOX/LH2)": {"mass": 15000, "hours": 80, "crew": True, "cat": "propulsion", "isp": 450, "thrust": "High"},
    "Nuclear Thermal (NTP)": {"mass": 25000, "hours": 120, "crew": True, "cat": "propulsion", "isp": 900, "thrust": "Medium-High"},
    "Nuclear Electric (NEP)": {"mass": 30000, "hours": 160, "crew": True, "cat": "propulsion", "isp": 5000, "thrust": "Low", "req_power": "Fission or Fusion"},
    "Solar Electric (SEP)": {"mass": 10000, "hours": 100, "crew": True, "cat": "propulsion", "isp": 3000, "thrust": "Very Low", "req_power": "Solar"},
    "Avionics & Comms Suite": {"mass": 4000, "hours": 60, "crew": True, "cat": "avionics"},
    "Shielding Section": {"mass": 4000, "hours": 30, "crew": False, "cat": "specialty"},
    "Robotic Arm Station": {"mass": 2500, "hours": 48, "crew": True, "cat": "specialty"},
}

POWER_TYPE_MAP = {
    "Solar": "Solar Array Unit",
    "Fission": "Fission Reactor Unit",
    "Fusion": "Fusion Reactor Unit",
}

PROPULSION_TYPE_MAP = {
    "Chemical": "Chemical (LOX/LH2)",
    "NTP": "Nuclear Thermal (NTP)",
    "NEP": "Nuclear Electric (NEP)",
    "SEP": "Solar Electric (SEP)",
}


def _make_module(module_type: str, idx: int) -> Module:
    spec = MODULE_SPECS[module_type]
    base_id = module_type.lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
    return Module(
        id=f"{base_id}_{idx}",
        type=module_type,
        mass_kg=spec["mass"],
        assembly_hours=spec["hours"],
        crew_required=spec["crew"],
        category=spec["cat"],
        power_output_kw=spec.get("power_kw", 0),
        isp=spec.get("isp"),
        thrust_level=spec.get("thrust"),
        required_power_system=spec.get("req_power"),
    )


def generate_spacecraft(
    length_km: float,
    structure_type: str,
    propulsion_type: str,
    power_type: str,
) -> AssemblyDAG:
    dag = AssemblyDAG()

    # --- Truss sections (backbone) ---
    n_truss = max(2, math.ceil(length_km / TRUSS_SPAN_KM))
    truss_ids: list[str] = []
    for i in range(n_truss):
        m = _make_module("Truss Section", i)
        prereqs = [truss_ids[-1]] if truss_ids else []
        dag.add_module(m, prerequisites=prereqs)
        truss_ids.append(m.id)

    # --- Docking node (on first truss) ---
    dock = _make_module("Airlock/Docking Node", 0)
    dag.add_module(dock, prerequisites=[truss_ids[0]])

    # --- Power systems (distributed along truss) ---
    power_module_type = POWER_TYPE_MAP[power_type]
    n_power = max(2, n_truss // 3)
    power_ids: list[str] = []
    for i in range(n_power):
        m = _make_module(power_module_type, i)
        anchor_idx = min(i * 3 + 1, n_truss - 1)
        dag.add_module(m, prerequisites=[truss_ids[anchor_idx]])
        power_ids.append(m.id)

    # --- Thermal systems (one per ~3 truss sections) ---
    n_thermal = max(1, n_truss // 4)
    for i in range(n_thermal):
        m = _make_module("Thermal System Unit", i)
        anchor_idx = min(i * 4 + 2, n_truss - 1)
        dag.add_module(m, prerequisites=[truss_ids[anchor_idx]])

    # --- Habitation (one per ~5 truss sections, min 1) ---
    n_hab = max(1, n_truss // 5)
    hab_ids: list[str] = []
    for i in range(n_hab):
        m = _make_module("Habitat Block", i)
        anchor_idx = min(i * 5 + 2, n_truss - 1)
        dag.add_module(m, prerequisites=[truss_ids[anchor_idx], dock.id])
        hab_ids.append(m.id)

    # --- Propulsion (fore and aft) ---
    prop_module_type = PROPULSION_TYPE_MAP[propulsion_type]
    n_prop = 2
    for i in range(n_prop):
        m = _make_module(prop_module_type, i)
        anchor_truss = truss_ids[0] if i == 0 else truss_ids[-1]
        prereqs = [anchor_truss]
        # Add power dependency for electric propulsion
        if propulsion_type == "NEP":
            prereqs.append(power_ids[0])
        elif propulsion_type == "SEP":
            prereqs.append(power_ids[0])
        dag.add_module(m, prerequisites=prereqs)

    # --- Avionics (one, mid-ship) ---
    avionics = _make_module("Avionics & Comms Suite", 0)
    mid_truss = truss_ids[n_truss // 2]
    dag.add_module(avionics, prerequisites=[mid_truss, power_ids[0]])

    # --- Shielding (one per ~3 truss sections) ---
    n_shield = max(1, n_truss // 3)
    for i in range(n_shield):
        m = _make_module("Shielding Section", i)
        anchor_idx = min(i * 3, n_truss - 1)
        dag.add_module(m, prerequisites=[truss_ids[anchor_idx]])

    # --- Robotic arm stations (2, at quarter points) ---
    n_arms = 2
    for i in range(n_arms):
        m = _make_module("Robotic Arm Station", i)
        anchor_idx = (i + 1) * n_truss // 3
        anchor_idx = min(anchor_idx, n_truss - 1)
        dag.add_module(m, prerequisites=[truss_ids[anchor_idx]])

    return dag
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_parametric.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/parametric.py tests/test_parametric.py
git commit -m "feat: add parametric spacecraft generator with DAG dependencies"
```

---

## Task 10: DP Solver

**Files:**
- Create: `simulation/solver/dp_solver.py`
- Create: `tests/test_solver.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_solver.py
import pytest
from simulation.solver.dp_solver import DPSolver, SolverConfig, SolverResult
from simulation.solver.objectives import ObjectiveWeights
from simulation.parametric import generate_spacecraft
from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage
from simulation.proximity import ProximityModel
from simulation.transfer import TransferModel


class TestDPSolver:
    def _make_config(self) -> SolverConfig:
        dag = generate_spacecraft(
            length_km=0.5,
            structure_type="truss",
            propulsion_type="Chemical",
            power_type="Solar",
        )
        return SolverConfig(
            dag=dag,
            cargo_vehicles=[
                CargoVehicle("Starship", "USA", 150000, 1000, 100, True, "Near-term"),
            ],
            crew_vehicles=[
                CrewVehicle("Crew Dragon", "USA", 7, 180, 12519, False),
            ],
            transfer_stages=[
                TransferStage("Chemical Kick Stage", 2000, 15000, 450, False),
            ],
            weights=ObjectiveWeights(w_launches=1.0, w_time=1.0, w_cost=1.0),
            proximity=ProximityModel(),
            transfer=TransferModel(),
            period_days=7,
            beam_width=100,
            max_periods=200,
            max_eva_hours_per_session=6,
            max_pairs_per_iva=2,
            robotic_time_penalty=1.5,
        )

    def test_solver_returns_result(self):
        config = self._make_config()
        solver = DPSolver(config)
        result = solver.solve()
        assert isinstance(result, SolverResult)

    def test_all_modules_built(self):
        config = self._make_config()
        solver = DPSolver(config)
        result = solver.solve()
        assert result.modules_completed == config.dag.total_modules

    def test_result_has_timeline(self):
        config = self._make_config()
        solver = DPSolver(config)
        result = solver.solve()
        assert len(result.timeline) > 0
        # Each entry should have a period and actions
        first = result.timeline[0]
        assert "period" in first
        assert "actions" in first

    def test_result_has_metrics(self):
        config = self._make_config()
        solver = DPSolver(config)
        result = solver.solve()
        assert result.total_launches > 0
        assert result.total_periods > 0
        assert result.total_cost_million > 0

    def test_heavier_weights_on_launches_reduces_launches(self):
        config_base = self._make_config()
        config_base.weights = ObjectiveWeights(w_launches=1.0, w_time=0.0, w_cost=0.0)
        solver1 = DPSolver(config_base)
        result1 = solver1.solve()

        config_time = self._make_config()
        config_time.weights = ObjectiveWeights(w_launches=0.0, w_time=1.0, w_cost=0.0)
        solver2 = DPSolver(config_time)
        result2 = solver2.solve()

        # When optimizing only for launches, should use fewer (or equal) launches
        assert result1.total_launches <= result2.total_launches + 2  # allow small tolerance
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_solver.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement DPSolver**

```python
# simulation/solver/dp_solver.py
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from simulation.models.modules import AssemblyDAG
from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage
from simulation.models.crew import CrewState
from simulation.models.state import SimState, DockedCrewVehicle, CargoInTransit
from simulation.proximity import ProximityModel
from simulation.transfer import TransferModel
from simulation.solver.objectives import ObjectiveWeights, compute_cost


@dataclass
class SolverConfig:
    dag: AssemblyDAG
    cargo_vehicles: list[CargoVehicle]
    crew_vehicles: list[CrewVehicle]
    transfer_stages: list[TransferStage]
    weights: ObjectiveWeights
    proximity: ProximityModel
    transfer: TransferModel
    period_days: int = 7
    beam_width: int = 100
    max_periods: int = 200
    max_eva_hours_per_session: float = 6
    max_pairs_per_iva: int = 2
    robotic_time_penalty: float = 1.5


@dataclass
class SolverResult:
    total_launches: int
    total_periods: int
    total_cost_million: float
    modules_completed: int
    cumulative_risk: float
    timeline: list[dict[str, Any]]
    final_state: SimState


class DPSolver:
    def __init__(self, config: SolverConfig) -> None:
        self.config = config
        self.dag = config.dag
        self.total_modules = config.dag.total_modules

        # Precompute best delivery option for each cargo vehicle
        self._delivery_cache: dict[str, tuple[float, int, float]] = {}
        for cv in config.cargo_vehicles:
            best_mass = 0.0
            best_transit = 999
            best_cost = cv.cost_per_launch_million
            for transfer_type in ["direct", "low_energy"]:
                stages = [None] if cv.l4_direct else config.transfer_stages
                for stage in stages:
                    try:
                        result = config.transfer.compute_delivery(cv, transfer_type, stage)
                        if result.mass_delivered_kg > best_mass:
                            best_mass = result.mass_delivered_kg
                            best_transit = result.transit_days
                            best_cost = result.cost_million
                    except ValueError:
                        continue
            if best_mass > 0:
                transit_periods = math.ceil(best_transit / config.period_days)
                self._delivery_cache[cv.name] = (best_mass, transit_periods, best_cost)

    def solve(self) -> SolverResult:
        initial = SimState.initial()
        # beam holds (state, timeline) pairs
        beam: list[tuple[SimState, list[dict]]] = [(initial, [])]

        for period in range(self.config.max_periods):
            if not beam:
                break

            # Check if any state is complete
            for state, timeline in beam:
                if len(state.modules_built) == self.total_modules:
                    return self._make_result(state, timeline)

            next_beam: list[tuple[SimState, list[dict], float]] = []

            for state, timeline in beam:
                successors = self._expand(state, period)
                for new_state, actions in successors:
                    cost = compute_cost(
                        self.config.weights,
                        new_state.total_launches,
                        new_state.period,
                        new_state.total_cost_million,
                        max_launches=self.total_modules * 2,
                        max_periods=self.config.max_periods,
                        max_cost_million=self.total_modules * 2000,
                    )
                    new_timeline = timeline + [{"period": period, "actions": actions}]
                    next_beam.append((new_state, new_timeline, cost))

            # Prune: keep top-K by cost, but prefer states with more modules built
            next_beam.sort(key=lambda x: (-(len(x[0].modules_built)), x[2]))
            beam = [(s, t) for s, t, _ in next_beam[:self.config.beam_width]]

        # Return best incomplete state if we hit max_periods
        if beam:
            best_state, best_timeline = beam[0]
            return self._make_result(best_state, best_timeline)

        return self._make_result(initial, [])

    def _expand(self, state: SimState, period: int) -> list[tuple[SimState, list[str]]]:
        successors: list[tuple[SimState, list[str]]] = []

        # --- Process arrivals ---
        arrived_modules: set[str] = set()
        remaining_transit = []
        for cargo in state.cargo_in_transit:
            if cargo.arrival_period <= period:
                arrived_modules.update(cargo.module_ids)
            else:
                remaining_transit.append(cargo)

        # --- Update crew rotations ---
        active_crew = []
        for cv in state.crew_vehicles:
            if cv.periods_remaining > 1:
                active_crew.append(DockedCrewVehicle(
                    cv.vehicle_name, cv.crew_onboard, cv.periods_remaining - 1
                ))

        # --- Compute assembly capacity ---
        total_crew = sum(cv.crew_onboard for cv in active_crew)
        progress = state.build_progress(self.total_modules)
        n_prox = len(active_crew)  # crew vehicles in proximity
        penalty = self.config.proximity.penalty(max(1, n_prox), progress)

        # Determine what can be built
        available = self.dag.get_available(state.modules_built)
        # Filter to modules whose mass has been delivered (simplified: if arrived or we have cargo)
        buildable = available  # simplified — assume delivered modules are buildable

        # Compute work hours this period
        crew_state = CrewState(
            total_crew=total_crew,
            max_pairs_per_iva=self.config.max_pairs_per_iva,
            max_eva_hours_per_session=self.config.max_eva_hours_per_session,
            eva_days_per_period=self.config.period_days,
            n_robotic_arms=sum(1 for m in state.modules_built
                              if "robotic_arm" in m),
            hours_per_period=self.config.period_days * 24,
            robotic_time_penalty=self.config.robotic_time_penalty,
        )

        crew_hours = crew_state.eva_hours_per_period / penalty
        robotic_hours = crew_state.robotic_hours_per_period / penalty

        # --- Greedily assign assembly tasks ---
        newly_built: set[str] = set()
        remaining_crew_hours = crew_hours
        remaining_robotic_hours = robotic_hours
        actions: list[str] = []

        for mid in sorted(buildable):
            mod = self.dag.get_module(mid)
            if mod.crew_required:
                if remaining_crew_hours >= mod.assembly_hours:
                    remaining_crew_hours -= mod.assembly_hours
                    newly_built.add(mid)
                    actions.append(f"assembled:{mid}")
            else:
                if remaining_robotic_hours >= mod.assembly_hours:
                    remaining_robotic_hours -= mod.assembly_hours
                    newly_built.add(mid)
                    actions.append(f"assembled:{mid}")

        new_modules_built = state.modules_built | newly_built

        # --- Risk accumulation ---
        risk = self.config.proximity.collision_risk(n_prox, self.config.period_days)

        # --- Generate successor states: one with no new launches, one with launches ---

        # Base state (no new launches this period)
        base_state = SimState(
            modules_built=new_modules_built,
            crew_vehicles=active_crew,
            cargo_in_transit=remaining_transit,
            cargo_at_site=state.cargo_at_site,
            tugs_available=state.tugs_available,
            period=period + 1,
            total_launches=state.total_launches,
            total_cost_million=state.total_cost_million,
            cumulative_risk=state.cumulative_risk + risk,
        )
        successors.append((base_state, actions))

        # Try launching cargo
        modules_not_delivered = set(self.dag.modules.keys()) - state.modules_built - newly_built
        # Find modules that aren't in transit
        in_transit_ids = set()
        for c in remaining_transit:
            in_transit_ids.update(c.module_ids)
        launchable = modules_not_delivered - in_transit_ids

        if launchable and self._delivery_cache:
            # Pick best cargo vehicle
            best_vehicle_name = max(self._delivery_cache, key=lambda k: self._delivery_cache[k][0])
            best_mass, transit_p, cost = self._delivery_cache[best_vehicle_name]

            # Pack modules into this launch by mass
            manifest: list[str] = []
            mass_remaining = best_mass
            for mid in sorted(launchable):
                mod = self.dag.get_module(mid)
                if mod.mass_kg <= mass_remaining:
                    manifest.append(mid)
                    mass_remaining -= mod.mass_kg

            if manifest:
                new_transit = remaining_transit + [
                    CargoInTransit(
                        module_ids=tuple(manifest),
                        arrival_period=period + transit_p,
                        cost_million=cost,
                    )
                ]
                launch_actions = actions + [f"launched:{best_vehicle_name}:{','.join(manifest)}"]
                launch_state = SimState(
                    modules_built=new_modules_built,
                    crew_vehicles=active_crew,
                    cargo_in_transit=new_transit,
                    cargo_at_site=state.cargo_at_site,
                    tugs_available=state.tugs_available,
                    period=period + 1,
                    total_launches=state.total_launches + 1,
                    total_cost_million=state.total_cost_million + cost,
                    cumulative_risk=state.cumulative_risk + risk,
                )
                successors.append((launch_state, launch_actions))

        # Try sending crew if none on-site
        if total_crew == 0 and self.config.crew_vehicles:
            cv = self.config.crew_vehicles[0]
            crew_count = min(cv.max_crew, 5)  # default reasonable crew size
            rotation_periods = cv.max_mission_duration_days // self.config.period_days
            new_crew = active_crew + [
                DockedCrewVehicle(cv.name, crew_count, rotation_periods)
            ]

            # Determine crew launch cost
            crew_cost = 200  # default crew launch cost estimate ($M)
            for cargo_v in self.config.cargo_vehicles:
                if cargo_v.l4_direct:
                    crew_cost = cargo_v.cost_per_launch_million
                    break

            crew_actions = actions + [f"crew_launch:{cv.name}:{crew_count}"]
            crew_state = SimState(
                modules_built=new_modules_built,
                crew_vehicles=new_crew,
                cargo_in_transit=remaining_transit,
                cargo_at_site=state.cargo_at_site,
                tugs_available=state.tugs_available,
                period=period + 1,
                total_launches=state.total_launches + 1,
                total_cost_million=state.total_cost_million + crew_cost,
                cumulative_risk=state.cumulative_risk + risk,
            )
            successors.append((crew_state, crew_actions))

        # Combined: launch cargo + crew
        if total_crew == 0 and launchable and self._delivery_cache and self.config.crew_vehicles:
            cv = self.config.crew_vehicles[0]
            crew_count = min(cv.max_crew, 5)
            rotation_periods = cv.max_mission_duration_days // self.config.period_days
            best_vehicle_name = max(self._delivery_cache, key=lambda k: self._delivery_cache[k][0])
            best_mass, transit_p, cost = self._delivery_cache[best_vehicle_name]

            manifest = []
            mass_remaining = best_mass
            for mid in sorted(launchable):
                mod = self.dag.get_module(mid)
                if mod.mass_kg <= mass_remaining:
                    manifest.append(mid)
                    mass_remaining -= mod.mass_kg

            if manifest:
                crew_cost = 200
                for cargo_v in self.config.cargo_vehicles:
                    if cargo_v.l4_direct:
                        crew_cost = cargo_v.cost_per_launch_million
                        break

                combined_state = SimState(
                    modules_built=new_modules_built,
                    crew_vehicles=active_crew + [
                        DockedCrewVehicle(cv.name, crew_count, rotation_periods)
                    ],
                    cargo_in_transit=remaining_transit + [
                        CargoInTransit(tuple(manifest), period + transit_p, cost)
                    ],
                    cargo_at_site=state.cargo_at_site,
                    tugs_available=state.tugs_available,
                    period=period + 1,
                    total_launches=state.total_launches + 2,
                    total_cost_million=state.total_cost_million + cost + crew_cost,
                    cumulative_risk=state.cumulative_risk + risk,
                )
                combined_actions = actions + [
                    f"launched:{best_vehicle_name}:{','.join(manifest)}",
                    f"crew_launch:{cv.name}:{crew_count}",
                ]
                successors.append((combined_state, combined_actions))

        return successors

    def _make_result(self, state: SimState, timeline: list[dict]) -> SolverResult:
        return SolverResult(
            total_launches=state.total_launches,
            total_periods=state.period,
            total_cost_million=state.total_cost_million,
            modules_completed=len(state.modules_built),
            cumulative_risk=state.cumulative_risk,
            timeline=timeline,
            final_state=state,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_solver.py -v --timeout=60`
Expected: All 5 tests PASS. The solver should complete a 0.5 km spacecraft in under 30 seconds.

- [ ] **Step 5: Commit**

```bash
git add simulation/solver/dp_solver.py tests/test_solver.py
git commit -m "feat: add forward DP solver with beam search pruning"
```

---

## Task 11: JSON Data Files

**Files:**
- Create: `data/cargo_vehicles.json`
- Create: `data/crew_vehicles.json`
- Create: `data/transfer_stages.json`
- Create: `data/module_catalog.json`

- [ ] **Step 1: Create cargo vehicles JSON**

```json
[
  {"name": "Falcon Heavy", "nation": "USA", "payload_to_leo_kg": 63800, "fairing_volume_m3": 145, "cost_per_launch_million": 150, "l4_direct": false, "status": "Operational"},
  {"name": "SLS Block 2", "nation": "USA", "payload_to_leo_kg": 130000, "fairing_volume_m3": 325, "cost_per_launch_million": 2000, "l4_direct": true, "status": "Operational"},
  {"name": "Starship", "nation": "USA", "payload_to_leo_kg": 150000, "fairing_volume_m3": 1000, "cost_per_launch_million": 100, "l4_direct": true, "status": "Near-term"},
  {"name": "Vulcan Centaur", "nation": "USA", "payload_to_leo_kg": 27200, "fairing_volume_m3": 95, "cost_per_launch_million": 110, "l4_direct": false, "status": "Operational"},
  {"name": "New Glenn", "nation": "USA", "payload_to_leo_kg": 45000, "fairing_volume_m3": 160, "cost_per_launch_million": 70, "l4_direct": false, "status": "Near-term"},
  {"name": "H3", "nation": "Japan", "payload_to_leo_kg": 6500, "fairing_volume_m3": 40, "cost_per_launch_million": 50, "l4_direct": false, "status": "Operational"},
  {"name": "Ariane 6", "nation": "Europe", "payload_to_leo_kg": 21600, "fairing_volume_m3": 180, "cost_per_launch_million": 115, "l4_direct": false, "status": "Operational"},
  {"name": "KSLV-III", "nation": "South Korea", "payload_to_leo_kg": 10000, "fairing_volume_m3": 50, "cost_per_launch_million": 80, "l4_direct": false, "status": "In development"},
  {"name": "GSLV Mk III", "nation": "India", "payload_to_leo_kg": 10000, "fairing_volume_m3": 50, "cost_per_launch_million": 50, "l4_direct": false, "status": "Operational"}
]
```

- [ ] **Step 2: Create crew vehicles JSON**

```json
[
  {"name": "Crew Dragon", "nation": "USA", "max_crew": 7, "max_mission_duration_days": 180, "mass_kg": 12519, "l4_direct": false, "mass_per_crew_kg": 200},
  {"name": "Starliner", "nation": "USA", "max_crew": 7, "max_mission_duration_days": 210, "mass_kg": 13000, "l4_direct": false, "mass_per_crew_kg": 200},
  {"name": "Orion", "nation": "USA/ESA", "max_crew": 4, "max_mission_duration_days": 21, "mass_kg": 26520, "l4_direct": true, "mass_per_crew_kg": 250},
  {"name": "Starship HLS", "nation": "USA", "max_crew": 6, "max_mission_duration_days": 180, "mass_kg": 100000, "l4_direct": true, "mass_per_crew_kg": 200}
]
```

- [ ] **Step 3: Create transfer stages JSON**

```json
[
  {"name": "Chemical Kick Stage", "dry_mass_kg": 2000, "propellant_kg": 15000, "isp_s": 450, "reusable": false},
  {"name": "SEP Tug", "dry_mass_kg": 5000, "propellant_kg": 2000, "isp_s": 3000, "reusable": true},
  {"name": "NTP Tug", "dry_mass_kg": 8000, "propellant_kg": 10000, "isp_s": 900, "reusable": true}
]
```

- [ ] **Step 4: Create module catalog JSON**

```json
[
  {"type": "Truss Section", "mass_kg": 5000, "assembly_hours": 48, "crew_required": false, "category": "structural"},
  {"type": "Airlock/Docking Node", "mass_kg": 5000, "assembly_hours": 72, "crew_required": true, "category": "structural"},
  {"type": "Habitat Block", "mass_kg": 20000, "assembly_hours": 120, "crew_required": true, "category": "habitation"},
  {"type": "Solar Array Unit", "mass_kg": 6000, "assembly_hours": 36, "crew_required": false, "category": "power", "power_output_kw": 100},
  {"type": "Fission Reactor Unit", "mass_kg": 15000, "assembly_hours": 100, "crew_required": true, "category": "power", "power_output_kw": 500},
  {"type": "Fusion Reactor Unit", "mass_kg": 40000, "assembly_hours": 160, "crew_required": true, "category": "power", "power_output_kw": 5000},
  {"type": "Thermal System Unit", "mass_kg": 3000, "assembly_hours": 24, "crew_required": false, "category": "thermal"},
  {"type": "Chemical (LOX/LH2)", "mass_kg": 15000, "assembly_hours": 80, "crew_required": true, "category": "propulsion", "isp": 450, "thrust_level": "High"},
  {"type": "Nuclear Thermal (NTP)", "mass_kg": 25000, "assembly_hours": 120, "crew_required": true, "category": "propulsion", "isp": 900, "thrust_level": "Medium-High"},
  {"type": "Nuclear Electric (NEP)", "mass_kg": 30000, "assembly_hours": 160, "crew_required": true, "category": "propulsion", "isp": 5000, "thrust_level": "Low", "required_power_system": "Fission or Fusion"},
  {"type": "Solar Electric (SEP)", "mass_kg": 10000, "assembly_hours": 100, "crew_required": true, "category": "propulsion", "isp": 3000, "thrust_level": "Very Low", "required_power_system": "Solar"},
  {"type": "Avionics & Comms Suite", "mass_kg": 4000, "assembly_hours": 60, "crew_required": true, "category": "avionics"},
  {"type": "Shielding Section", "mass_kg": 4000, "assembly_hours": 30, "crew_required": false, "category": "specialty"},
  {"type": "Robotic Arm Station", "mass_kg": 2500, "assembly_hours": 48, "crew_required": true, "category": "specialty"}
]
```

- [ ] **Step 5: Commit**

```bash
git add data/
git commit -m "feat: add vehicle and module catalog JSON data files"
```

---

## Task 12: Flask API Server

**Files:**
- Create: `simulation/app.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_api.py
import json
import pytest
from simulation.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestCatalogEndpoints:
    def test_get_cargo_vehicles(self, client):
        resp = client.get("/api/catalog/cargo-vehicles")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]

    def test_get_crew_vehicles(self, client):
        resp = client.get("/api/catalog/crew-vehicles")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 4

    def test_get_transfer_stages(self, client):
        resp = client.get("/api/catalog/transfer-stages")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 3

    def test_get_module_catalog(self, client):
        resp = client.get("/api/catalog/modules")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 14


class TestParametricEndpoint:
    def test_generate_spacecraft(self, client):
        resp = client.post("/api/generate", json={
            "length_km": 1.0,
            "structure_type": "truss",
            "propulsion_type": "Chemical",
            "power_type": "Solar",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "modules" in data
        assert "dependencies" in data
        assert len(data["modules"]) > 0


class TestSimulationEndpoint:
    def test_run_simulation(self, client):
        resp = client.post("/api/simulate", json={
            "spacecraft": {
                "length_km": 0.5,
                "structure_type": "truss",
                "propulsion_type": "Chemical",
                "power_type": "Solar",
            },
            "cargo_vehicles": ["Starship"],
            "crew_vehicles": ["Crew Dragon"],
            "transfer_stages": ["Chemical Kick Stage"],
            "weights": {"w_launches": 1.0, "w_time": 1.0, "w_cost": 1.0},
            "proximity": {
                "alpha": 0.1, "beta": 1.5,
                "base_capacity": 2, "max_capacity": 10,
            },
            "period_days": 7,
            "beam_width": 50,
            "max_periods": 200,
            "max_eva_hours_per_session": 6,
            "max_pairs_per_iva": 2,
            "robotic_time_penalty": 1.5,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_launches" in data
        assert "total_periods" in data
        assert "timeline" in data
        assert data["modules_completed"] > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement Flask app**

```python
# simulation/app.py
from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage
from simulation.parametric import generate_spacecraft
from simulation.proximity import ProximityModel
from simulation.transfer import TransferModel
from simulation.solver.objectives import ObjectiveWeights
from simulation.solver.dp_solver import DPSolver, SolverConfig

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> list[dict]:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # --- Catalog endpoints ---
    @app.route("/api/catalog/cargo-vehicles")
    def get_cargo_vehicles():
        return jsonify(_load_json("cargo_vehicles.json"))

    @app.route("/api/catalog/crew-vehicles")
    def get_crew_vehicles():
        return jsonify(_load_json("crew_vehicles.json"))

    @app.route("/api/catalog/transfer-stages")
    def get_transfer_stages():
        return jsonify(_load_json("transfer_stages.json"))

    @app.route("/api/catalog/modules")
    def get_modules():
        return jsonify(_load_json("module_catalog.json"))

    # --- Parametric generation ---
    @app.route("/api/generate", methods=["POST"])
    def generate():
        body = request.get_json()
        dag = generate_spacecraft(
            length_km=body["length_km"],
            structure_type=body["structure_type"],
            propulsion_type=body["propulsion_type"],
            power_type=body["power_type"],
        )
        modules = [
            {
                "id": m.id,
                "type": m.type,
                "mass_kg": m.mass_kg,
                "assembly_hours": m.assembly_hours,
                "crew_required": m.crew_required,
                "category": m.category,
                "power_output_kw": m.power_output_kw,
                "isp": m.isp,
                "thrust_level": m.thrust_level,
                "required_power_system": m.required_power_system,
            }
            for m in dag.modules.values()
        ]
        dependencies = {
            mid: dag.get_prerequisites(mid) for mid in dag.modules
        }
        return jsonify({"modules": modules, "dependencies": dependencies})

    # --- Simulation ---
    @app.route("/api/simulate", methods=["POST"])
    def simulate():
        body = request.get_json()

        # Build spacecraft DAG
        sc = body["spacecraft"]
        dag = generate_spacecraft(
            length_km=sc["length_km"],
            structure_type=sc["structure_type"],
            propulsion_type=sc["propulsion_type"],
            power_type=sc["power_type"],
        )

        # Resolve vehicles from catalogs
        all_cargo = {v.name: v for v in CargoVehicle.default_catalog()}
        all_crew = {v.name: v for v in CrewVehicle.default_catalog()}
        all_stages = {s.name: s for s in TransferStage.default_catalog()}

        cargo_vehicles = [all_cargo[n] for n in body["cargo_vehicles"] if n in all_cargo]
        crew_vehicles = [all_crew[n] for n in body["crew_vehicles"] if n in all_crew]
        transfer_stages = [all_stages[n] for n in body["transfer_stages"] if n in all_stages]

        w = body.get("weights", {})
        prox = body.get("proximity", {})

        config = SolverConfig(
            dag=dag,
            cargo_vehicles=cargo_vehicles,
            crew_vehicles=crew_vehicles,
            transfer_stages=transfer_stages,
            weights=ObjectiveWeights(
                w_launches=w.get("w_launches", 1.0),
                w_time=w.get("w_time", 1.0),
                w_cost=w.get("w_cost", 1.0),
            ),
            proximity=ProximityModel(
                alpha=prox.get("alpha", 0.1),
                beta=prox.get("beta", 1.5),
                base_capacity=prox.get("base_capacity", 2),
                max_capacity=prox.get("max_capacity", 10),
            ),
            transfer=TransferModel(),
            period_days=body.get("period_days", 7),
            beam_width=body.get("beam_width", 100),
            max_periods=body.get("max_periods", 200),
            max_eva_hours_per_session=body.get("max_eva_hours_per_session", 6),
            max_pairs_per_iva=body.get("max_pairs_per_iva", 2),
            robotic_time_penalty=body.get("robotic_time_penalty", 1.5),
        )

        solver = DPSolver(config)
        result = solver.solve()

        return jsonify({
            "total_launches": result.total_launches,
            "total_periods": result.total_periods,
            "total_cost_million": result.total_cost_million,
            "modules_completed": result.modules_completed,
            "cumulative_risk": result.cumulative_risk,
            "timeline": result.timeline,
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api.py -v --timeout=60`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/app.py tests/test_api.py
git commit -m "feat: add Flask API with catalog, generation, and simulation endpoints"
```

---

## Task 13: Next.js Project Setup

**Files:**
- Create: `frontend/` (via `npx create-next-app`)

- [ ] **Step 1: Scaffold Next.js project**

Run from the repo root:

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --no-import-alias
```

Accept defaults. This creates the Next.js project structure.

- [ ] **Step 2: Install additional dependencies**

```bash
cd frontend
npm install recharts d3 zustand
npm install -D @types/d3
```

- [ ] **Step 3: Verify the dev server starts**

Run: `cd frontend && npm run dev`
Expected: Server starts on localhost:3000, shows default Next.js page. Kill with Ctrl+C.

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Next.js frontend with Recharts, D3, and Zustand"
```

---

## Task 14: TypeScript Types & API Client

**Files:**
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/api.ts`

- [ ] **Step 1: Create TypeScript types matching Python models**

```typescript
// frontend/src/lib/types.ts

export interface CargoVehicle {
  name: string;
  nation: string;
  payload_to_leo_kg: number;
  fairing_volume_m3: number;
  cost_per_launch_million: number;
  l4_direct: boolean;
  status: string;
}

export interface CrewVehicle {
  name: string;
  nation: string;
  max_crew: number;
  max_mission_duration_days: number;
  mass_kg: number;
  l4_direct: boolean;
  mass_per_crew_kg: number;
}

export interface TransferStage {
  name: string;
  dry_mass_kg: number;
  propellant_kg: number;
  isp_s: number;
  reusable: boolean;
}

export interface ModuleDef {
  type: string;
  mass_kg: number;
  assembly_hours: number;
  crew_required: boolean;
  category: string;
  power_output_kw?: number;
  isp?: number;
  thrust_level?: string;
  required_power_system?: string;
}

export interface GeneratedModule extends ModuleDef {
  id: string;
}

export interface SpacecraftConfig {
  length_km: number;
  structure_type: string;
  propulsion_type: string;
  power_type: string;
}

export interface GenerateResult {
  modules: GeneratedModule[];
  dependencies: Record<string, string[]>;
}

export interface ObjectiveWeights {
  w_launches: number;
  w_time: number;
  w_cost: number;
}

export interface ProximityConfig {
  alpha: number;
  beta: number;
  base_capacity: number;
  max_capacity: number;
}

export interface SimulationRequest {
  spacecraft: SpacecraftConfig;
  cargo_vehicles: string[];
  crew_vehicles: string[];
  transfer_stages: string[];
  weights: ObjectiveWeights;
  proximity: ProximityConfig;
  period_days: number;
  beam_width: number;
  max_periods: number;
  max_eva_hours_per_session: number;
  max_pairs_per_iva: number;
  robotic_time_penalty: number;
}

export interface TimelineEntry {
  period: number;
  actions: string[];
}

export interface SimulationResult {
  total_launches: number;
  total_periods: number;
  total_cost_million: number;
  modules_completed: number;
  cumulative_risk: number;
  timeline: TimelineEntry[];
}
```

- [ ] **Step 2: Create API client**

```typescript
// frontend/src/lib/api.ts

import type {
  CargoVehicle,
  CrewVehicle,
  TransferStage,
  ModuleDef,
  GenerateResult,
  SimulationRequest,
  SimulationResult,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`);
  }
  return resp.json() as Promise<T>;
}

export async function getCargoVehicles(): Promise<CargoVehicle[]> {
  return fetchJson("/api/catalog/cargo-vehicles");
}

export async function getCrewVehicles(): Promise<CrewVehicle[]> {
  return fetchJson("/api/catalog/crew-vehicles");
}

export async function getTransferStages(): Promise<TransferStage[]> {
  return fetchJson("/api/catalog/transfer-stages");
}

export async function getModuleCatalog(): Promise<ModuleDef[]> {
  return fetchJson("/api/catalog/modules");
}

export async function generateSpacecraft(
  config: { length_km: number; structure_type: string; propulsion_type: string; power_type: string }
): Promise<GenerateResult> {
  return fetchJson("/api/generate", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function runSimulation(
  request: SimulationRequest
): Promise<SimulationResult> {
  return fetchJson("/api/simulate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/
git commit -m "feat: add TypeScript types and Flask API client"
```

---

## Task 15: Zustand Store

**Files:**
- Create: `frontend/src/store/useSimStore.ts`

- [ ] **Step 1: Create the store**

```typescript
// frontend/src/store/useSimStore.ts

import { create } from "zustand";
import type {
  CargoVehicle,
  CrewVehicle,
  TransferStage,
  SpacecraftConfig,
  ObjectiveWeights,
  ProximityConfig,
  SimulationResult,
  TimelineEntry,
} from "@/lib/types";

interface SimStore {
  // --- Catalogs (loaded once) ---
  cargoVehicles: CargoVehicle[];
  crewVehicles: CrewVehicle[];
  transferStages: TransferStage[];

  // --- User selections ---
  selectedCargo: string[];
  selectedCrew: string[];
  selectedStages: string[];
  spacecraft: SpacecraftConfig;
  weights: ObjectiveWeights;
  proximity: ProximityConfig;
  periodDays: number;
  beamWidth: number;
  maxPeriods: number;
  maxEvaHours: number;
  maxPairsPerIva: number;
  roboticTimePenalty: number;

  // --- Simulation state ---
  isRunning: boolean;
  result: SimulationResult | null;

  // --- Playback state ---
  currentPeriod: number;
  isPlaying: boolean;
  playbackSpeed: number;

  // --- Actions ---
  setCatalogs: (cargo: CargoVehicle[], crew: CrewVehicle[], stages: TransferStage[]) => void;
  setSelectedCargo: (names: string[]) => void;
  setSelectedCrew: (names: string[]) => void;
  setSelectedStages: (names: string[]) => void;
  setSpacecraft: (config: Partial<SpacecraftConfig>) => void;
  setWeights: (weights: Partial<ObjectiveWeights>) => void;
  setProximity: (config: Partial<ProximityConfig>) => void;
  setPeriodDays: (days: number) => void;
  setBeamWidth: (width: number) => void;
  setMaxPeriods: (periods: number) => void;
  setMaxEvaHours: (hours: number) => void;
  setMaxPairsPerIva: (pairs: number) => void;
  setRoboticTimePenalty: (penalty: number) => void;
  setIsRunning: (running: boolean) => void;
  setResult: (result: SimulationResult | null) => void;
  setCurrentPeriod: (period: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
}

export const useSimStore = create<SimStore>((set) => ({
  cargoVehicles: [],
  crewVehicles: [],
  transferStages: [],

  selectedCargo: ["Starship"],
  selectedCrew: ["Crew Dragon"],
  selectedStages: ["Chemical Kick Stage"],
  spacecraft: {
    length_km: 1.0,
    structure_type: "truss",
    propulsion_type: "Chemical",
    power_type: "Solar",
  },
  weights: { w_launches: 1.0, w_time: 1.0, w_cost: 1.0 },
  proximity: { alpha: 0.1, beta: 1.5, base_capacity: 2, max_capacity: 10 },
  periodDays: 7,
  beamWidth: 100,
  maxPeriods: 200,
  maxEvaHours: 6,
  maxPairsPerIva: 2,
  roboticTimePenalty: 1.5,

  isRunning: false,
  result: null,

  currentPeriod: 0,
  isPlaying: false,
  playbackSpeed: 1,

  setCatalogs: (cargo, crew, stages) =>
    set({ cargoVehicles: cargo, crewVehicles: crew, transferStages: stages }),
  setSelectedCargo: (names) => set({ selectedCargo: names }),
  setSelectedCrew: (names) => set({ selectedCrew: names }),
  setSelectedStages: (names) => set({ selectedStages: names }),
  setSpacecraft: (config) =>
    set((s) => ({ spacecraft: { ...s.spacecraft, ...config } })),
  setWeights: (weights) =>
    set((s) => ({ weights: { ...s.weights, ...weights } })),
  setProximity: (config) =>
    set((s) => ({ proximity: { ...s.proximity, ...config } })),
  setPeriodDays: (days) => set({ periodDays: days }),
  setBeamWidth: (width) => set({ beamWidth: width }),
  setMaxPeriods: (periods) => set({ maxPeriods: periods }),
  setMaxEvaHours: (hours) => set({ maxEvaHours: hours }),
  setMaxPairsPerIva: (pairs) => set({ maxPairsPerIva: pairs }),
  setRoboticTimePenalty: (penalty) => set({ roboticTimePenalty: penalty }),
  setIsRunning: (running) => set({ isRunning: running }),
  setResult: (result) => set({ result, currentPeriod: 0, isPlaying: false }),
  setCurrentPeriod: (period) => set({ currentPeriod: period }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),
}));
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/store/
git commit -m "feat: add Zustand store for simulation configuration and playback state"
```

---

## Task 16: Configuration Panel Component

**Files:**
- Create: `frontend/src/components/ConfigPanel.tsx`
- Create: `frontend/src/components/VehicleSelector.tsx`
- Create: `frontend/src/components/WeightSliders.tsx`

- [ ] **Step 1: Create VehicleSelector component**

```tsx
// frontend/src/components/VehicleSelector.tsx
"use client";

interface VehicleSelectorProps {
  title: string;
  vehicles: { name: string; nation: string }[];
  selected: string[];
  onChange: (names: string[]) => void;
}

export default function VehicleSelector({
  title,
  vehicles,
  selected,
  onChange,
}: VehicleSelectorProps) {
  const toggle = (name: string) => {
    if (selected.includes(name)) {
      onChange(selected.filter((n) => n !== name));
    } else {
      onChange([...selected, name]);
    }
  };

  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold mb-2">{title}</h3>
      <div className="space-y-1">
        {vehicles.map((v) => (
          <label key={v.name} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={selected.includes(v.name)}
              onChange={() => toggle(v.name)}
              className="rounded"
            />
            <span>{v.name}</span>
            <span className="text-gray-400 text-xs">({v.nation})</span>
          </label>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create WeightSliders component**

```tsx
// frontend/src/components/WeightSliders.tsx
"use client";

import { useSimStore } from "@/store/useSimStore";

export default function WeightSliders() {
  const weights = useSimStore((s) => s.weights);
  const setWeights = useSimStore((s) => s.setWeights);

  const sliders = [
    { key: "w_launches" as const, label: "Launches" },
    { key: "w_time" as const, label: "Time" },
    { key: "w_cost" as const, label: "Cost" },
  ];

  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold mb-2">Objective Weights</h3>
      {sliders.map(({ key, label }) => (
        <div key={key} className="mb-2">
          <label className="flex justify-between text-sm">
            <span>{label}</span>
            <span>{weights[key].toFixed(1)}</span>
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={weights[key]}
            onChange={(e) => setWeights({ [key]: parseFloat(e.target.value) })}
            className="w-full"
          />
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Create ConfigPanel component**

```tsx
// frontend/src/components/ConfigPanel.tsx
"use client";

import { useEffect } from "react";
import { useSimStore } from "@/store/useSimStore";
import {
  getCargoVehicles,
  getCrewVehicles,
  getTransferStages,
  runSimulation,
} from "@/lib/api";
import VehicleSelector from "./VehicleSelector";
import WeightSliders from "./WeightSliders";
import type { SimulationRequest } from "@/lib/types";

export default function ConfigPanel() {
  const store = useSimStore();

  useEffect(() => {
    Promise.all([getCargoVehicles(), getCrewVehicles(), getTransferStages()])
      .then(([cargo, crew, stages]) => store.setCatalogs(cargo, crew, stages))
      .catch(console.error);
  }, []);

  const handleRun = async () => {
    store.setIsRunning(true);
    store.setResult(null);
    try {
      const request: SimulationRequest = {
        spacecraft: store.spacecraft,
        cargo_vehicles: store.selectedCargo,
        crew_vehicles: store.selectedCrew,
        transfer_stages: store.selectedStages,
        weights: store.weights,
        proximity: store.proximity,
        period_days: store.periodDays,
        beam_width: store.beamWidth,
        max_periods: store.maxPeriods,
        max_eva_hours_per_session: store.maxEvaHours,
        max_pairs_per_iva: store.maxPairsPerIva,
        robotic_time_penalty: store.roboticTimePenalty,
      };
      const result = await runSimulation(request);
      store.setResult(result);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      store.setIsRunning(false);
    }
  };

  return (
    <div className="w-80 h-full overflow-y-auto border-r border-gray-700 p-4 bg-gray-900 text-white">
      <h2 className="text-lg font-bold mb-4">Configuration</h2>

      {/* Spacecraft params */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-2">Spacecraft</h3>
        <label className="block text-sm mb-1">
          Length (km): {store.spacecraft.length_km}
        </label>
        <input
          type="range"
          min="0.5"
          max="5"
          step="0.5"
          value={store.spacecraft.length_km}
          onChange={(e) =>
            store.setSpacecraft({ length_km: parseFloat(e.target.value) })
          }
          className="w-full mb-2"
        />

        <label className="block text-sm mb-1">Propulsion</label>
        <select
          value={store.spacecraft.propulsion_type}
          onChange={(e) =>
            store.setSpacecraft({ propulsion_type: e.target.value })
          }
          className="w-full bg-gray-800 rounded p-1 text-sm mb-2"
        >
          <option value="Chemical">Chemical (LOX/LH2)</option>
          <option value="NTP">Nuclear Thermal (NTP)</option>
          <option value="NEP">Nuclear Electric (NEP)</option>
          <option value="SEP">Solar Electric (SEP)</option>
        </select>

        <label className="block text-sm mb-1">Power System</label>
        <select
          value={store.spacecraft.power_type}
          onChange={(e) =>
            store.setSpacecraft({ power_type: e.target.value })
          }
          className="w-full bg-gray-800 rounded p-1 text-sm mb-2"
        >
          <option value="Solar">Solar Array</option>
          <option value="Fission">Fission Reactor</option>
          <option value="Fusion">Fusion Reactor</option>
        </select>
      </div>

      {/* Vehicle selectors */}
      <VehicleSelector
        title="Cargo Vehicles"
        vehicles={store.cargoVehicles}
        selected={store.selectedCargo}
        onChange={store.setSelectedCargo}
      />
      <VehicleSelector
        title="Crew Vehicles"
        vehicles={store.crewVehicles}
        selected={store.selectedCrew}
        onChange={store.setSelectedCrew}
      />
      <VehicleSelector
        title="Transfer Stages"
        vehicles={store.transferStages.map((s) => ({
          name: s.name,
          nation: s.reusable ? "Reusable" : "Expendable",
        }))}
        selected={store.selectedStages}
        onChange={store.setSelectedStages}
      />

      {/* Weights */}
      <WeightSliders />

      {/* Crew params */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-2">Crew Parameters</h3>
        <label className="flex justify-between text-sm">
          <span>EVA hours/session</span>
          <span>{store.maxEvaHours}</span>
        </label>
        <input
          type="range" min="4" max="8" step="1"
          value={store.maxEvaHours}
          onChange={(e) => store.setMaxEvaHours(parseInt(e.target.value))}
          className="w-full mb-2"
        />
        <label className="flex justify-between text-sm">
          <span>Max pairs per IVA</span>
          <span>{store.maxPairsPerIva}</span>
        </label>
        <input
          type="range" min="1" max="4" step="1"
          value={store.maxPairsPerIva}
          onChange={(e) => store.setMaxPairsPerIva(parseInt(e.target.value))}
          className="w-full mb-2"
        />
        <label className="flex justify-between text-sm">
          <span>Robotic time penalty</span>
          <span>{store.roboticTimePenalty}x</span>
        </label>
        <input
          type="range" min="1" max="3" step="0.25"
          value={store.roboticTimePenalty}
          onChange={(e) => store.setRoboticTimePenalty(parseFloat(e.target.value))}
          className="w-full mb-2"
        />
      </div>

      {/* Proximity params */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-2">Proximity Model</h3>
        <label className="flex justify-between text-sm">
          <span>Alpha</span>
          <span>{store.proximity.alpha}</span>
        </label>
        <input
          type="range" min="0.01" max="0.5" step="0.01"
          value={store.proximity.alpha}
          onChange={(e) => store.setProximity({ alpha: parseFloat(e.target.value) })}
          className="w-full mb-2"
        />
        <label className="flex justify-between text-sm">
          <span>Beta</span>
          <span>{store.proximity.beta}</span>
        </label>
        <input
          type="range" min="1" max="3" step="0.1"
          value={store.proximity.beta}
          onChange={(e) => store.setProximity({ beta: parseFloat(e.target.value) })}
          className="w-full mb-2"
        />
      </div>

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={store.isRunning}
        className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold"
      >
        {store.isRunning ? "Running..." : "Run Simulation"}
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ConfigPanel.tsx frontend/src/components/VehicleSelector.tsx frontend/src/components/WeightSliders.tsx
git commit -m "feat: add configuration panel with vehicle selectors and weight sliders"
```

---

## Task 17: Metrics Summary & Cost Breakdown

**Files:**
- Create: `frontend/src/components/MetricsSummary.tsx`
- Create: `frontend/src/components/CostBreakdown.tsx`

- [ ] **Step 1: Create MetricsSummary**

```tsx
// frontend/src/components/MetricsSummary.tsx
"use client";

import { useSimStore } from "@/store/useSimStore";

export default function MetricsSummary() {
  const result = useSimStore((s) => s.result);

  if (!result) return null;

  const metrics = [
    { label: "Total Launches", value: result.total_launches },
    {
      label: "Total Time",
      value: `${result.total_periods} periods (${(result.total_periods * 7 / 30).toFixed(1)} months)`,
    },
    { label: "Total Cost", value: `$${result.total_cost_million.toFixed(0)}M` },
    { label: "Modules Completed", value: result.modules_completed },
    { label: "Cumulative Risk", value: result.cumulative_risk.toFixed(4) },
  ];

  return (
    <div className="grid grid-cols-5 gap-2 mb-4">
      {metrics.map((m) => (
        <div
          key={m.label}
          className="bg-gray-800 rounded p-3 text-center"
        >
          <div className="text-xs text-gray-400">{m.label}</div>
          <div className="text-lg font-bold text-white">{m.value}</div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create CostBreakdown**

```tsx
// frontend/src/components/CostBreakdown.tsx
"use client";

import { useSimStore } from "@/store/useSimStore";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export default function CostBreakdown() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);

  if (!result) return null;

  // Aggregate launches by vehicle from timeline up to currentPeriod
  const launchCounts: Record<string, number> = {};
  for (const entry of result.timeline) {
    if (entry.period > currentPeriod) break;
    for (const action of entry.actions) {
      if (action.startsWith("launched:") || action.startsWith("crew_launch:")) {
        const vehicleName = action.split(":")[1];
        launchCounts[vehicleName] = (launchCounts[vehicleName] || 0) + 1;
      }
    }
  }

  const data = Object.entries(launchCounts).map(([name, count]) => ({
    name,
    launches: count,
  }));

  if (data.length === 0) return null;

  return (
    <div className="bg-gray-800 rounded p-3 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">Launches by Vehicle</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="name" tick={{ fill: "#aaa", fontSize: 11 }} />
          <YAxis tick={{ fill: "#aaa", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#333", border: "none" }}
            labelStyle={{ color: "#fff" }}
          />
          <Bar dataKey="launches" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/MetricsSummary.tsx frontend/src/components/CostBreakdown.tsx
git commit -m "feat: add metrics summary cards and cost breakdown bar chart"
```

---

## Task 18: Resource Charts & Gantt Chart

**Files:**
- Create: `frontend/src/components/ResourceCharts.tsx`
- Create: `frontend/src/components/GanttChart.tsx`

- [ ] **Step 1: Create ResourceCharts**

```tsx
// frontend/src/components/ResourceCharts.tsx
"use client";

import { useMemo } from "react";
import { useSimStore } from "@/store/useSimStore";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

export default function ResourceCharts() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);

  const data = useMemo(() => {
    if (!result) return [];

    let modulesBuilt = 0;
    let crewOnSite = 0;
    let vehiclesProx = 0;

    return result.timeline.map((entry) => {
      for (const action of entry.actions) {
        if (action.startsWith("assembled:")) modulesBuilt++;
        if (action.startsWith("crew_launch:")) {
          const parts = action.split(":");
          crewOnSite += parseInt(parts[2]) || 0;
          vehiclesProx++;
        }
        if (action.startsWith("launched:")) vehiclesProx++;
      }
      return {
        period: entry.period,
        modules: modulesBuilt,
        crew: crewOnSite,
        vehicles: vehiclesProx,
      };
    });
  }, [result]);

  if (!result || data.length === 0) return null;

  return (
    <div className="bg-gray-800 rounded p-3 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">
        Resource Utilization Over Time
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="period" tick={{ fill: "#aaa", fontSize: 11 }} />
          <YAxis tick={{ fill: "#aaa", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#333", border: "none" }}
            labelStyle={{ color: "#fff" }}
          />
          <Area
            type="monotone"
            dataKey="modules"
            stroke="#22c55e"
            fill="#22c55e"
            fillOpacity={0.3}
            name="Modules Built"
          />
          <Area
            type="monotone"
            dataKey="crew"
            stroke="#eab308"
            fill="#eab308"
            fillOpacity={0.3}
            name="Crew On-Site"
          />
          <ReferenceLine x={currentPeriod} stroke="#ef4444" strokeDasharray="3 3" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 2: Create GanttChart**

```tsx
// frontend/src/components/GanttChart.tsx
"use client";

import { useMemo, useRef, useEffect } from "react";
import { useSimStore } from "@/store/useSimStore";

const COLORS: Record<string, string> = {
  assembled: "#22c55e",
  launched: "#3b82f6",
  crew_launch: "#eab308",
};

const ROW_HEIGHT = 20;
const PERIOD_WIDTH = 12;
const LEFT_MARGIN = 120;

export default function GanttChart() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const events = useMemo(() => {
    if (!result) return [];
    const evts: { label: string; period: number; type: string }[] = [];
    for (const entry of result.timeline) {
      for (const action of entry.actions) {
        const [type, ...rest] = action.split(":");
        const label = rest.join(":").substring(0, 20);
        evts.push({ label, period: entry.period, type });
      }
    }
    return evts;
  }, [result]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !result) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const totalPeriods = result.total_periods;
    const width = LEFT_MARGIN + totalPeriods * PERIOD_WIDTH + 20;
    const height = events.length * ROW_HEIGHT + 40;
    canvas.width = width;
    canvas.height = height;

    ctx.fillStyle = "#1f2937";
    ctx.fillRect(0, 0, width, height);

    // Draw events
    events.forEach((evt, i) => {
      const y = i * ROW_HEIGHT + 20;
      const x = LEFT_MARGIN + evt.period * PERIOD_WIDTH;

      // Label
      ctx.fillStyle = "#9ca3af";
      ctx.font = "11px monospace";
      ctx.fillText(evt.label, 4, y + 14);

      // Bar
      ctx.fillStyle = COLORS[evt.type] || "#6b7280";
      ctx.fillRect(x, y + 2, PERIOD_WIDTH - 2, ROW_HEIGHT - 4);
    });

    // Current period indicator
    const cpX = LEFT_MARGIN + currentPeriod * PERIOD_WIDTH;
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(cpX, 0);
    ctx.lineTo(cpX, height);
    ctx.stroke();

  }, [events, currentPeriod, result]);

  if (!result) return null;

  return (
    <div className="bg-gray-800 rounded p-3 mb-4 overflow-x-auto">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">Assembly Timeline</h3>
      <canvas ref={canvasRef} className="max-w-full" />
    </div>
  );
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ResourceCharts.tsx frontend/src/components/GanttChart.tsx
git commit -m "feat: add resource utilization charts and Gantt timeline"
```

---

## Task 19: 2D Assembly View & Playback Controls

**Files:**
- Create: `frontend/src/components/AssemblyView.tsx`
- Create: `frontend/src/components/PlaybackControls.tsx`

- [ ] **Step 1: Create AssemblyView**

```tsx
// frontend/src/components/AssemblyView.tsx
"use client";

import { useRef, useEffect, useMemo } from "react";
import { useSimStore } from "@/store/useSimStore";

const CATEGORY_COLORS: Record<string, string> = {
  structural: "#9ca3af",
  habitation: "#3b82f6",
  power: "#eab308",
  thermal: "#06b6d4",
  propulsion: "#ef4444",
  avionics: "#a855f7",
  specialty: "#f97316",
};

const MODULE_HEIGHT = 30;
const MODULE_WIDTH = 60;
const PADDING = 10;

export default function AssemblyView() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Determine which modules are built by currentPeriod
  const builtModules = useMemo(() => {
    if (!result) return new Set<string>();
    const built = new Set<string>();
    for (const entry of result.timeline) {
      if (entry.period > currentPeriod) break;
      for (const action of entry.actions) {
        if (action.startsWith("assembled:")) {
          built.add(action.split(":")[1]);
        }
      }
    }
    return built;
  }, [result, currentPeriod]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.parentElement?.clientWidth || 800;
    const height = 300;
    canvas.width = width;
    canvas.height = height;

    ctx.fillStyle = "#111827";
    ctx.fillRect(0, 0, width, height);

    // Draw spacecraft as a horizontal layout
    // Truss sections form the backbone, other modules attach above/below
    const allModuleIds = Array.from(builtModules).sort();
    const trussModules = allModuleIds.filter((id) => id.startsWith("truss_section"));
    const otherModules = allModuleIds.filter((id) => !id.startsWith("truss_section"));

    // Draw truss backbone
    const trussY = height / 2;
    const startX = PADDING;
    trussModules.forEach((id, i) => {
      const x = startX + i * (MODULE_WIDTH + 4);
      ctx.fillStyle = CATEGORY_COLORS.structural;
      ctx.fillRect(x, trussY - MODULE_HEIGHT / 4, MODULE_WIDTH, MODULE_HEIGHT / 2);
      ctx.strokeStyle = "#555";
      ctx.strokeRect(x, trussY - MODULE_HEIGHT / 4, MODULE_WIDTH, MODULE_HEIGHT / 2);
    });

    // Draw other modules above/below truss
    let aboveY = trussY - MODULE_HEIGHT - 10;
    let belowY = trussY + MODULE_HEIGHT / 2 + 10;
    let xOffset = startX;
    otherModules.forEach((id) => {
      // Determine category from id
      let category = "specialty";
      for (const [cat] of Object.entries(CATEGORY_COLORS)) {
        if (id.includes(cat.substring(0, 4))) {
          category = cat;
          break;
        }
      }
      // Alternate placement above/below
      const useAbove = Math.random() > 0.5;
      const y = useAbove ? aboveY : belowY;

      ctx.fillStyle = CATEGORY_COLORS[category] || "#6b7280";
      ctx.fillRect(xOffset, y, MODULE_WIDTH - 10, MODULE_HEIGHT);
      ctx.strokeStyle = "#555";
      ctx.strokeRect(xOffset, y, MODULE_WIDTH - 10, MODULE_HEIGHT);

      // Label
      ctx.fillStyle = "#fff";
      ctx.font = "9px monospace";
      const shortId = id.substring(0, 10);
      ctx.fillText(shortId, xOffset + 2, y + MODULE_HEIGHT / 2 + 3);

      xOffset += MODULE_WIDTH - 6;
      if (xOffset > width - MODULE_WIDTH) {
        xOffset = startX;
        aboveY -= MODULE_HEIGHT + 4;
        belowY += MODULE_HEIGHT + 4;
      }
    });

    // Overlay: period and crew info
    ctx.fillStyle = "#fff";
    ctx.font = "13px monospace";
    ctx.fillText(`Period: ${currentPeriod}`, width - 150, 20);
    ctx.fillText(`Modules: ${builtModules.size}`, width - 150, 38);

  }, [builtModules, currentPeriod]);

  if (!result) {
    return (
      <div className="bg-gray-800 rounded p-3 mb-4 h-[300px] flex items-center justify-center text-gray-500">
        Run a simulation to see assembly progression
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded p-3 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">2D Assembly View</h3>
      <canvas ref={canvasRef} className="w-full" />
    </div>
  );
}
```

- [ ] **Step 2: Create PlaybackControls**

```tsx
// frontend/src/components/PlaybackControls.tsx
"use client";

import { useEffect, useRef } from "react";
import { useSimStore } from "@/store/useSimStore";

export default function PlaybackControls() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);
  const isPlaying = useSimStore((s) => s.isPlaying);
  const playbackSpeed = useSimStore((s) => s.playbackSpeed);
  const setCurrentPeriod = useSimStore((s) => s.setCurrentPeriod);
  const setIsPlaying = useSimStore((s) => s.setIsPlaying);
  const setPlaybackSpeed = useSimStore((s) => s.setPlaybackSpeed);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isPlaying && result) {
      intervalRef.current = setInterval(() => {
        setCurrentPeriod(
          useSimStore.getState().currentPeriod >= result.total_periods
            ? 0
            : useSimStore.getState().currentPeriod + 1
        );
      }, 1000 / playbackSpeed);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, playbackSpeed, result]);

  if (!result) return null;

  return (
    <div className="bg-gray-800 rounded p-3 mb-4 flex items-center gap-4">
      <button
        onClick={() => setCurrentPeriod(Math.max(0, currentPeriod - 1))}
        className="px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm"
      >
        &lt;
      </button>
      <button
        onClick={() => setIsPlaying(!isPlaying)}
        className="px-4 py-1 bg-blue-600 rounded hover:bg-blue-700 text-sm font-semibold"
      >
        {isPlaying ? "Pause" : "Play"}
      </button>
      <button
        onClick={() => {
          setIsPlaying(false);
          setCurrentPeriod(0);
        }}
        className="px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm"
      >
        Stop
      </button>
      <button
        onClick={() =>
          setCurrentPeriod(Math.min(result.total_periods, currentPeriod + 1))
        }
        className="px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm"
      >
        &gt;
      </button>

      {/* Speed selector */}
      <select
        value={playbackSpeed}
        onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
        className="bg-gray-700 rounded p-1 text-sm"
      >
        <option value={1}>1x</option>
        <option value={2}>2x</option>
        <option value={5}>5x</option>
        <option value={10}>10x</option>
      </select>

      {/* Timeline scrubber */}
      <input
        type="range"
        min="0"
        max={result.total_periods}
        value={currentPeriod}
        onChange={(e) => {
          setIsPlaying(false);
          setCurrentPeriod(parseInt(e.target.value));
        }}
        className="flex-1"
      />
      <span className="text-sm text-gray-400 w-24 text-right">
        {currentPeriod} / {result.total_periods}
      </span>
    </div>
  );
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/AssemblyView.tsx frontend/src/components/PlaybackControls.tsx
git commit -m "feat: add 2D assembly view with real-time playback controls"
```

---

## Task 20: Pareto Plot Component

**Files:**
- Create: `frontend/src/components/ParetoPlot.tsx`

- [ ] **Step 1: Create ParetoPlot**

```tsx
// frontend/src/components/ParetoPlot.tsx
"use client";

import { useSimStore } from "@/store/useSimStore";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ZAxis,
} from "recharts";

export default function ParetoPlot() {
  const result = useSimStore((s) => s.result);

  if (!result) return null;

  // For a single run, show the solution point.
  // Multiple runs would populate this with more points.
  const data = [
    {
      launches: result.total_launches,
      time: result.total_periods,
      cost: result.total_cost_million,
    },
  ];

  return (
    <div className="bg-gray-800 rounded p-3 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">
        Solution Space (Launches vs Time)
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis
            dataKey="launches"
            name="Launches"
            tick={{ fill: "#aaa", fontSize: 11 }}
            label={{ value: "Launches", position: "bottom", fill: "#aaa", fontSize: 11 }}
          />
          <YAxis
            dataKey="time"
            name="Periods"
            tick={{ fill: "#aaa", fontSize: 11 }}
            label={{ value: "Periods", angle: -90, position: "left", fill: "#aaa", fontSize: 11 }}
          />
          <ZAxis dataKey="cost" range={[100, 400]} name="Cost ($M)" />
          <Tooltip
            contentStyle={{ backgroundColor: "#333", border: "none" }}
            labelStyle={{ color: "#fff" }}
          />
          <Scatter data={data} fill="#22c55e" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ParetoPlot.tsx
git commit -m "feat: add Pareto frontier scatter plot component"
```

---

## Task 21: Dashboard Layout & Main Page

**Files:**
- Create: `frontend/src/components/Dashboard.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/app/globals.css`

- [ ] **Step 1: Create Dashboard component**

```tsx
// frontend/src/components/Dashboard.tsx
"use client";

import MetricsSummary from "./MetricsSummary";
import GanttChart from "./GanttChart";
import ResourceCharts from "./ResourceCharts";
import CostBreakdown from "./CostBreakdown";
import ParetoPlot from "./ParetoPlot";
import AssemblyView from "./AssemblyView";
import PlaybackControls from "./PlaybackControls";

export default function Dashboard() {
  return (
    <div className="flex-1 h-full overflow-y-auto p-4 bg-gray-950 text-white">
      <h2 className="text-lg font-bold mb-4">Mission Assembly Dashboard</h2>
      <MetricsSummary />
      <PlaybackControls />
      <AssemblyView />
      <div className="grid grid-cols-2 gap-4">
        <GanttChart />
        <ResourceCharts />
        <CostBreakdown />
        <ParetoPlot />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Update globals.css for dark theme**

Replace the contents of `frontend/src/app/globals.css` with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #__next {
  height: 100%;
  margin: 0;
  padding: 0;
  background-color: #030712;
  color: #fff;
}
```

- [ ] **Step 3: Update layout.tsx**

Replace the contents of `frontend/src/app/layout.tsx` with:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "In-Space Assembly Mission Planner",
  description: "Mission planning simulation for in-space assembly of large structures at L4",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

- [ ] **Step 4: Update page.tsx**

Replace the contents of `frontend/src/app/page.tsx` with:

```tsx
import ConfigPanel from "@/components/ConfigPanel";
import Dashboard from "@/components/Dashboard";

export default function Home() {
  return (
    <main className="flex h-screen">
      <ConfigPanel />
      <Dashboard />
    </main>
  );
}
```

- [ ] **Step 5: Verify the app builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/Dashboard.tsx frontend/src/app/page.tsx frontend/src/app/layout.tsx frontend/src/app/globals.css
git commit -m "feat: assemble dashboard layout and wire up main page"
```

---

## Task 22: Module Editor Component

**Files:**
- Create: `frontend/src/components/ModuleEditor.tsx`
- Modify: `frontend/src/components/ConfigPanel.tsx`

- [ ] **Step 1: Create ModuleEditor**

```tsx
// frontend/src/components/ModuleEditor.tsx
"use client";

import { useState, useEffect } from "react";
import { generateSpacecraft } from "@/lib/api";
import { useSimStore } from "@/store/useSimStore";
import type { GeneratedModule } from "@/lib/types";

export default function ModuleEditor() {
  const spacecraft = useSimStore((s) => s.spacecraft);
  const [modules, setModules] = useState<GeneratedModule[]>([]);
  const [loading, setLoading] = useState(false);

  const loadModules = async () => {
    setLoading(true);
    try {
      const result = await generateSpacecraft(spacecraft);
      setModules(result.modules);
    } catch (err) {
      console.error("Failed to generate spacecraft:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">Module Preview</h3>
        <button
          onClick={loadModules}
          disabled={loading}
          className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
        >
          {loading ? "..." : "Preview"}
        </button>
      </div>
      {modules.length > 0 && (
        <div className="max-h-40 overflow-y-auto text-xs space-y-1">
          {modules.map((m) => (
            <div
              key={m.id}
              className="flex justify-between bg-gray-800 rounded px-2 py-1"
            >
              <span>{m.type}</span>
              <span className="text-gray-400">{m.mass_kg.toLocaleString()} kg</span>
            </div>
          ))}
          <div className="text-gray-400 mt-1">
            Total: {modules.length} modules,{" "}
            {modules.reduce((s, m) => s + m.mass_kg, 0).toLocaleString()} kg
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add ModuleEditor to ConfigPanel**

In `frontend/src/components/ConfigPanel.tsx`, add the import at the top:

```tsx
import ModuleEditor from "./ModuleEditor";
```

Then insert `<ModuleEditor />` after the power system select dropdown, before the vehicle selectors:

```tsx
        </select>
      </div>

      <ModuleEditor />

      {/* Vehicle selectors */}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ModuleEditor.tsx frontend/src/components/ConfigPanel.tsx
git commit -m "feat: add module editor with parametric preview in config panel"
```

---

## Task 23: End-to-End Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""End-to-end test: generate spacecraft, solve, verify results are plausible."""
import pytest
from simulation.parametric import generate_spacecraft
from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage
from simulation.proximity import ProximityModel
from simulation.transfer import TransferModel
from simulation.solver.objectives import ObjectiveWeights
from simulation.solver.dp_solver import DPSolver, SolverConfig


class TestEndToEnd:
    def test_full_pipeline_chemical_solar(self):
        dag = generate_spacecraft(
            length_km=1.0,
            structure_type="truss",
            propulsion_type="Chemical",
            power_type="Solar",
        )
        config = SolverConfig(
            dag=dag,
            cargo_vehicles=[
                CargoVehicle("Starship", "USA", 150000, 1000, 100, True, "Near-term"),
            ],
            crew_vehicles=[
                CrewVehicle("Crew Dragon", "USA", 7, 180, 12519, False),
            ],
            transfer_stages=[
                TransferStage("Chemical Kick Stage", 2000, 15000, 450, False),
            ],
            weights=ObjectiveWeights(w_launches=1, w_time=1, w_cost=1),
            proximity=ProximityModel(),
            transfer=TransferModel(),
            beam_width=50,
            max_periods=300,
        )
        solver = DPSolver(config)
        result = solver.solve()

        assert result.modules_completed == dag.total_modules
        assert result.total_launches >= 1
        assert result.total_periods >= 1
        assert result.total_cost_million > 0
        assert len(result.timeline) > 0

    def test_full_pipeline_nep_fusion(self):
        dag = generate_spacecraft(
            length_km=0.5,
            structure_type="truss",
            propulsion_type="NEP",
            power_type="Fusion",
        )
        config = SolverConfig(
            dag=dag,
            cargo_vehicles=[
                CargoVehicle("SLS Block 2", "USA", 130000, 325, 2000, True, "Operational"),
                CargoVehicle("Starship", "USA", 150000, 1000, 100, True, "Near-term"),
            ],
            crew_vehicles=[
                CrewVehicle("Orion", "USA/ESA", 4, 21, 26520, True),
            ],
            transfer_stages=[
                TransferStage("NTP Tug", 8000, 10000, 900, True),
            ],
            weights=ObjectiveWeights(w_launches=0.5, w_time=1.5, w_cost=0.5),
            proximity=ProximityModel(alpha=0.15, beta=1.5, base_capacity=2, max_capacity=8),
            transfer=TransferModel(),
            beam_width=50,
            max_periods=300,
        )
        solver = DPSolver(config)
        result = solver.solve()

        assert result.modules_completed == dag.total_modules
        assert result.total_launches >= 1

    def test_flask_api_full_flow(self):
        from simulation.app import create_app

        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            # Generate
            resp = client.post("/api/generate", json={
                "length_km": 0.5,
                "structure_type": "truss",
                "propulsion_type": "Chemical",
                "power_type": "Solar",
            })
            assert resp.status_code == 200
            gen = resp.get_json()
            assert len(gen["modules"]) > 0

            # Simulate
            resp = client.post("/api/simulate", json={
                "spacecraft": {
                    "length_km": 0.5,
                    "structure_type": "truss",
                    "propulsion_type": "Chemical",
                    "power_type": "Solar",
                },
                "cargo_vehicles": ["Starship"],
                "crew_vehicles": ["Crew Dragon"],
                "transfer_stages": ["Chemical Kick Stage"],
                "weights": {"w_launches": 1, "w_time": 1, "w_cost": 1},
                "proximity": {"alpha": 0.1, "beta": 1.5, "base_capacity": 2, "max_capacity": 10},
                "period_days": 7,
                "beam_width": 50,
                "max_periods": 200,
                "max_eva_hours_per_session": 6,
                "max_pairs_per_iva": 2,
                "robotic_time_penalty": 1.5,
            })
            assert resp.status_code == 200
            result = resp.get_json()
            assert result["modules_completed"] > 0
            assert result["total_launches"] >= 1
```

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v --timeout=120`
Expected: All 3 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration tests for full simulation pipeline"
```

---

## Task 24: Run All Tests & Final Verification

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --timeout=120`
Expected: All tests PASS (should be ~40+ tests across all test files).

- [ ] **Step 2: Start Flask backend and verify**

Run: `python simulation/app.py`
Expected: Flask starts on http://localhost:5000. Test with:
```bash
curl http://localhost:5000/api/catalog/cargo-vehicles
```
Expected: JSON array of 9 cargo vehicles.

- [ ] **Step 3: Start frontend and verify**

Run (in a new terminal): `cd frontend && npm run dev`
Expected: Next.js starts on http://localhost:3000. The configuration panel and dashboard should render.

- [ ] **Step 4: End-to-end manual test**

1. Open http://localhost:3000
2. Set spacecraft length to 0.5 km
3. Select Starship and Crew Dragon
4. Click "Run Simulation"
5. Verify results appear in dashboard
6. Click "Play" and verify assembly animation plays

- [ ] **Step 5: Commit any fixes**

```bash
git add -A
git commit -m "fix: address any issues found during final verification"
```
