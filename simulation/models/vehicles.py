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
    # Minimum periods from campaign start before first launch is allowed
    lead_time_periods: int = 4
    # Fractional cost premium applied only on the first flight (integration/
    # contracting overhead amortized over one flight)
    first_flight_cost_premium: float = 0.08

    @property
    def first_flight_cost_million(self) -> float:
        return self.cost_per_launch_million * (1.0 + self.first_flight_cost_premium)

    @staticmethod
    def default_catalog() -> list[CargoVehicle]:
        return [
            # Operational: ~1-2 month contract/manifest lead, 8-12% integration premium
            # Falcon Heavy expendable: ~$150M (NASA PSYCHE 2023 reference)
            CargoVehicle("Falcon Heavy",   "USA",         63800,  145,  150,  False, "Operational",    lead_time_periods=4,  first_flight_cost_premium=0.08),
            # SLS Block 2: NASA OIG 2023 reported ~$4.1B per launch for Block 1; Block 2 similar
            CargoVehicle("SLS Block 2",    "USA",         130000, 325,  4100, True,  "Operational",    lead_time_periods=26, first_flight_cost_premium=0.12),
            # Vulcan Centaur Heavy (VC6): ULA list price ~$130–185M for heavy config
            CargoVehicle("Vulcan Centaur", "USA",         27200,  95,   130,  False, "Operational",    lead_time_periods=8,  first_flight_cost_premium=0.08),
            # H3-24: JAXA target ~¥7B ≈ $47M; rounded to $50M
            CargoVehicle("H3",             "Japan",       6500,   40,   50,   False, "Operational",    lead_time_periods=13, first_flight_cost_premium=0.10),
            # Ariane 64 (heavy): ESA ~$110M commercial catalog price
            CargoVehicle("Ariane 6",       "Europe",      21600,  180,  110,  False, "Operational",    lead_time_periods=13, first_flight_cost_premium=0.10),
            # GSLV Mk III / LVM3: ISRO commercial list ~$35–50M
            CargoVehicle("GSLV Mk III",    "India",       10000,  50,   50,   False, "Operational",    lead_time_periods=13, first_flight_cost_premium=0.10),
            # Near-term: 3-6 month production/qualification lead, 20% premium
            # Starship: SpaceX commercial target ~$100M for early operational flights
            CargoVehicle("Starship",       "USA",         150000, 1000, 100,  True,  "Near-term",      lead_time_periods=18, first_flight_cost_premium=0.20),
            # New Glenn: Blue Origin commercial list ~$90M for early flights
            CargoVehicle("New Glenn",      "USA",         45000,  160,  90,   False, "Near-term",      lead_time_periods=13, first_flight_cost_premium=0.20),
            # In development: 18-month qualification + certification, 40% premium
            CargoVehicle("KSLV-III",       "South Korea", 10000,  50,   80,   False, "In development", lead_time_periods=78, first_flight_cost_premium=0.40),
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
    lead_time_periods: int = 8
    first_flight_cost_premium: float = 0.08

    @property
    def first_flight_cost_million(self) -> float:
        return self.cost_per_launch_million * (1.0 + self.first_flight_cost_premium)

    def available_cargo_kg(self, crew_onboard: int) -> float:
        return self.mass_kg - crew_onboard * self.mass_per_crew_kg

    @staticmethod
    def default_catalog() -> list[CrewVehicle]:
        return [
            # Crew Dragon on Falcon 9: NASA CCtCap ~$55M/seat × 4 crew ≈ $220M/mission
            CrewVehicle("Crew Dragon",  "USA",     7, 180, 12519,  False,  220.0, 200, lead_time_periods=8,  first_flight_cost_premium=0.08),
            # Starliner on Atlas V N22: ~$90M/seat × 4 crew ≈ $360M/mission
            CrewVehicle("Starliner",    "USA",     7, 210, 13000,  False,  360.0, 200, lead_time_periods=13, first_flight_cost_premium=0.10),
            # Orion capsule per mission (capsule only, not including SLS launch vehicle)
            CrewVehicle("Orion",        "USA/ESA", 4, 21,  26520,  True,   600.0, 250, lead_time_periods=26, first_flight_cost_premium=0.12),
            # Starship HLS: NASA demo contract ~$1.45B/mission; aspirational production target ~$250M
            CrewVehicle("Starship HLS", "USA",     6, 180, 100000, True,   250.0, 200, lead_time_periods=26, first_flight_cost_premium=0.20),
        ]


@dataclass(frozen=True)
class TransferStage:
    name: str
    dry_mass_kg: float
    propellant_kg: float
    isp_s: float
    reusable: bool
    lead_time_periods: int = 8
    first_flight_cost_premium: float = 0.10

    @staticmethod
    def default_catalog() -> list[TransferStage]:
        return [
            # Chemical kick stage: ~2 month manifest lead, standard integration premium
            TransferStage("Chemical Kick Stage", 2000,  15000, 450,  False, lead_time_periods=8,   first_flight_cost_premium=0.10),
            # SEP tug: complex solar-electric system, ~1 year development/integration
            TransferStage("SEP Tug",             5000,  2000,  3000, True,  lead_time_periods=52,  first_flight_cost_premium=0.25),
            # NTP tug: nuclear certification + safety review, ~2 year lead
            TransferStage("NTP Tug",             8000,  10000, 900,  True,  lead_time_periods=104, first_flight_cost_premium=0.40),
        ]
