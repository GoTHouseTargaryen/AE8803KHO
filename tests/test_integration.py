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
