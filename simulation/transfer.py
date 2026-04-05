from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from simulation.models.vehicles import CargoVehicle, TransferStage

G0_KMS2 = 9.80665e-3  # km/s^2

TRANSFER_OPTIONS = {
    "direct": {"delta_v_kms": 4.1, "transit_days": 60},
    "low_energy": {"delta_v_kms": 3.8, "transit_days": 120},
}

DEFAULT_DIRECT_ISP_S = 450


@dataclass
class DeliveryResult:
    mass_delivered_kg: float
    transit_days: int
    cost_million: float


class TransferModel:
    def compute_delivery(
        self,
        vehicle: CargoVehicle,
        transfer_type: str,
        transfer_stage: Optional[TransferStage],
    ) -> DeliveryResult:
        opts = TRANSFER_OPTIONS[transfer_type]
        delta_v = opts["delta_v_kms"]
        transit_days = opts["transit_days"]

        if vehicle.l4_direct:
            payload_leo = vehicle.payload_to_leo_kg
            isp = DEFAULT_DIRECT_ISP_S
            mass_delivered = payload_leo * math.exp(-delta_v / (isp * G0_KMS2))
            return DeliveryResult(
                mass_delivered_kg=mass_delivered,
                transit_days=transit_days,
                cost_million=vehicle.cost_per_launch_million,
            )

        if transfer_stage is None:
            raise ValueError(
                f"'{vehicle.name}' is LEO-only and requires a transfer stage for L4 delivery"
            )

        tug_total = transfer_stage.dry_mass_kg + transfer_stage.propellant_kg
        payload_for_tug = vehicle.payload_to_leo_kg - tug_total
        if payload_for_tug <= 0:
            return DeliveryResult(mass_delivered_kg=0, transit_days=transit_days,
                                  cost_million=vehicle.cost_per_launch_million)

        isp = transfer_stage.isp_s
        R = math.exp(delta_v / (isp * G0_KMS2))
        if R >= 1.0:
            cargo_max_by_tug = (R * transfer_stage.dry_mass_kg - tug_total) / (1 - R)
        else:
            cargo_max_by_tug = payload_for_tug

        if cargo_max_by_tug <= 0:
            return DeliveryResult(mass_delivered_kg=0, transit_days=transit_days,
                                  cost_million=vehicle.cost_per_launch_million)

        mass_delivered = min(payload_for_tug, cargo_max_by_tug)

        return DeliveryResult(
            mass_delivered_kg=mass_delivered,
            transit_days=transit_days,
            cost_million=vehicle.cost_per_launch_million,
        )
