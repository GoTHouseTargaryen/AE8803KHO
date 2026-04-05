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
