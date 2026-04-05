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
