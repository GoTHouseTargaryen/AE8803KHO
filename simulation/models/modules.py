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
