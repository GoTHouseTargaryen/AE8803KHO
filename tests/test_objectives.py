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
