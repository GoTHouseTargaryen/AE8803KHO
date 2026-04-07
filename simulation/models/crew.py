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
    duty_cycle: float = 0.6  # 60% productive after rest/maintenance overhead

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
        return self.n_eva_pairs * self.max_eva_hours_per_session * self.eva_days_per_period * self.duty_cycle

    @property
    def robotic_hours_per_period(self) -> float:
        return self.n_robotic_arms * self.hours_per_period / self.robotic_time_penalty
