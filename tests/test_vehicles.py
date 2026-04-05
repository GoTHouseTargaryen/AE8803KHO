from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage


class TestCargoVehicle:
    def test_create_cargo_vehicle(self):
        fh = CargoVehicle(
            name="Falcon Heavy",
            nation="USA",
            payload_to_leo_kg=63800,
            fairing_volume_m3=145,
            cost_per_launch_million=150,
            l4_direct=False,
            status="Operational",
        )
        assert fh.name == "Falcon Heavy"
        assert fh.l4_direct is False

    def test_all_catalog_vehicles(self):
        vehicles = CargoVehicle.default_catalog()
        names = [v.name for v in vehicles]
        assert "Falcon Heavy" in names
        assert "SLS Block 2" in names
        assert "Starship" in names
        assert "H3" in names
        assert "Ariane 6" in names
        assert "GSLV Mk III" in names
        assert len(vehicles) == 9


class TestCrewVehicle:
    def test_create_crew_vehicle(self):
        dragon = CrewVehicle(
            name="Crew Dragon",
            nation="USA",
            max_crew=7,
            max_mission_duration_days=180,
            mass_kg=12519,
            l4_direct=False,
            mass_per_crew_kg=200,
        )
        assert dragon.max_crew == 7

    def test_cargo_capacity_full_crew(self):
        dragon = CrewVehicle(
            name="Crew Dragon",
            nation="USA",
            max_crew=7,
            max_mission_duration_days=180,
            mass_kg=12519,
            l4_direct=False,
            mass_per_crew_kg=200,
        )
        cargo = dragon.available_cargo_kg(crew_onboard=7)
        assert cargo == 12519 - 7 * 200

    def test_cargo_capacity_partial_crew(self):
        dragon = CrewVehicle(
            name="Crew Dragon",
            nation="USA",
            max_crew=7,
            max_mission_duration_days=180,
            mass_kg=12519,
            l4_direct=False,
            mass_per_crew_kg=200,
        )
        cargo = dragon.available_cargo_kg(crew_onboard=4)
        assert cargo == 12519 - 4 * 200

    def test_default_catalog(self):
        vehicles = CrewVehicle.default_catalog()
        assert len(vehicles) == 4
        names = [v.name for v in vehicles]
        assert "Orion" in names


class TestTransferStage:
    def test_create_transfer_stage(self):
        tug = TransferStage(
            name="SEP Tug",
            dry_mass_kg=5000,
            propellant_kg=2000,
            isp_s=3000,
            reusable=True,
        )
        assert tug.reusable is True

    def test_default_catalog(self):
        stages = TransferStage.default_catalog()
        assert len(stages) == 3
        names = [s.name for s in stages]
        assert "Chemical Kick Stage" in names
        assert "NTP Tug" in names
