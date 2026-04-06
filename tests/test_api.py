# tests/test_api.py
import json
import pytest
from simulation.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestCatalogEndpoints:
    def test_get_cargo_vehicles(self, client):
        resp = client.get("/api/catalog/cargo-vehicles")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]

    def test_get_crew_vehicles(self, client):
        resp = client.get("/api/catalog/crew-vehicles")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 4

    def test_get_transfer_stages(self, client):
        resp = client.get("/api/catalog/transfer-stages")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 3

    def test_get_module_catalog(self, client):
        resp = client.get("/api/catalog/modules")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 14


class TestParametricEndpoint:
    def test_generate_spacecraft(self, client):
        resp = client.post("/api/generate", json={
            "length_km": 1.0,
            "structure_type": "truss",
            "propulsion_type": "Chemical",
            "power_type": "Solar",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "modules" in data
        assert "dependencies" in data
        assert len(data["modules"]) > 0


class TestSimulationEndpoint:
    def test_run_simulation(self, client):
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
            "weights": {"w_launches": 1.0, "w_time": 1.0, "w_cost": 1.0},
            "proximity": {
                "alpha": 0.1, "beta": 1.5,
                "base_capacity": 2, "max_capacity": 10,
            },
            "period_days": 7,
            "beam_width": 50,
            "max_periods": 200,
            "max_eva_hours_per_session": 6,
            "max_pairs_per_iva": 2,
            "robotic_time_penalty": 1.5,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_launches" in data
        assert "total_periods" in data
        assert "timeline" in data
        assert data["modules_completed"] > 0
