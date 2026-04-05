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
        n_pairs = n_vehicles * (n_vehicles - 1) / 2
        return self.collision_risk_coeff * n_pairs * period_length_days
