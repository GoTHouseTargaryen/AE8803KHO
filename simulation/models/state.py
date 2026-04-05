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
