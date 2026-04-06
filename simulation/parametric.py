# simulation/parametric.py
from __future__ import annotations

import math

from simulation.models.modules import Module, AssemblyDAG

TRUSS_SPAN_KM = 0.2

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
