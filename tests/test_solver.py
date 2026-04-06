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

        assert result1.total_launches <= result2.total_launches + 2
