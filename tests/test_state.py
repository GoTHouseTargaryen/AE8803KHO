# tests/test_state.py
from simulation.models.state import SimState, DockedCrewVehicle, CargoInTransit, Launch


class TestSimState:
    def test_initial_state(self):
        s = SimState.initial()
        assert s.modules_built == frozenset()
        assert s.period == 0
        assert s.total_launches == 0
        assert s.total_cost_million == 0

    def test_n_vehicles_prox(self):
        crew_v = DockedCrewVehicle(
            vehicle_name="Crew Dragon", crew_onboard=4, periods_remaining=10
        )
        s = SimState(
            modules_built=frozenset(),
            crew_vehicles=[crew_v],
            cargo_in_transit=[],
            cargo_at_site=0,
            tugs_available=0,
            period=0,
            total_launches=0,
            total_cost_million=0,
            cumulative_risk=0,
        )
        assert s.n_vehicles_prox == 1

    def test_total_crew(self):
        cv1 = DockedCrewVehicle(vehicle_name="Crew Dragon", crew_onboard=4, periods_remaining=10)
        cv2 = DockedCrewVehicle(vehicle_name="Starliner", crew_onboard=3, periods_remaining=8)
        s = SimState(
            modules_built=frozenset(),
            crew_vehicles=[cv1, cv2],
            cargo_in_transit=[],
            cargo_at_site=0,
            tugs_available=0,
            period=0,
            total_launches=0,
            total_cost_million=0,
            cumulative_risk=0,
        )
        assert s.total_crew == 7

    def test_build_progress(self):
        s = SimState(
            modules_built=frozenset({"a", "b"}),
            crew_vehicles=[],
            cargo_in_transit=[],
            cargo_at_site=0,
            tugs_available=0,
            period=0,
            total_launches=0,
            total_cost_million=0,
            cumulative_risk=0,
        )
        assert s.build_progress(total_modules=4) == 0.5
