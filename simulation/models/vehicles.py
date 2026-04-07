from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CargoVehicle:
    name: str
    nation: str
    payload_to_leo_kg: float
    fairing_volume_m3: float
    cost_per_launch_million: float
    l4_direct: bool
    status: str

    @staticmethod
    def default_catalog() -> list[CargoVehicle]:
        return [
            CargoVehicle("Falcon Heavy", "USA", 63800, 145, 150, False, "Operational"),
            CargoVehicle("SLS Block 2", "USA", 130000, 325, 2000, True, "Operational"),
            CargoVehicle("Starship", "USA", 150000, 1000, 100, True, "Near-term"),
            CargoVehicle("Vulcan Centaur", "USA", 27200, 95, 110, False, "Operational"),
            CargoVehicle("New Glenn", "USA", 45000, 160, 70, False, "Near-term"),
            CargoVehicle("H3", "Japan", 6500, 40, 50, False, "Operational"),
            CargoVehicle("Ariane 6", "Europe", 21600, 180, 115, False, "Operational"),
            CargoVehicle("KSLV-III", "South Korea", 10000, 50, 80, False, "In development"),
            CargoVehicle("GSLV Mk III", "India", 10000, 50, 50, False, "Operational"),
        ]


@dataclass(frozen=True)
class CrewVehicle:
    name: str
    nation: str
    max_crew: int
    max_mission_duration_days: int
    mass_kg: float
    l4_direct: bool
    cost_per_launch_million: float = 200.0
    mass_per_crew_kg: float = 200

    def available_cargo_kg(self, crew_onboard: int) -> float:
        return self.mass_kg - crew_onboard * self.mass_per_crew_kg

    @staticmethod
    def default_catalog() -> list[CrewVehicle]:
        return [
            CrewVehicle("Crew Dragon", "USA", 7, 180, 12519, False, 55.0),
            CrewVehicle("Starliner", "USA", 7, 210, 13000, False, 90.0),
            CrewVehicle("Orion", "USA/ESA", 4, 21, 26520, True, 500.0),
            CrewVehicle("Starship HLS", "USA", 6, 180, 100000, True, 200.0),
        ]


@dataclass(frozen=True)
class TransferStage:
    name: str
    dry_mass_kg: float
    propellant_kg: float
    isp_s: float
    reusable: bool

    @staticmethod
    def default_catalog() -> list[TransferStage]:
        return [
            TransferStage("Chemical Kick Stage", 2000, 15000, 450, False),
            TransferStage("SEP Tug", 5000, 2000, 3000, True),
            TransferStage("NTP Tug", 8000, 10000, 900, True),
        ]
