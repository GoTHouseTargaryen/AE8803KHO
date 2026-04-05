import pytest
from simulation.transfer import TransferModel
from simulation.models.vehicles import CargoVehicle, TransferStage


class TestTransferModel:
    def test_direct_capable_vehicle(self):
        sls = CargoVehicle("SLS Block 2", "USA", 130000, 325, 2000, True, "Operational")
        tm = TransferModel()
        result = tm.compute_delivery(sls, transfer_type="direct", transfer_stage=None)
        assert result.mass_delivered_kg > 0
        assert result.mass_delivered_kg < 130000
        assert result.transit_days == 60

    def test_low_energy_transfer(self):
        sls = CargoVehicle("SLS Block 2", "USA", 130000, 325, 2000, True, "Operational")
        tm = TransferModel()
        result_direct = tm.compute_delivery(sls, transfer_type="direct", transfer_stage=None)
        result_low = tm.compute_delivery(sls, transfer_type="low_energy", transfer_stage=None)
        assert result_low.mass_delivered_kg > result_direct.mass_delivered_kg
        assert result_low.transit_days == 120

    def test_leo_only_vehicle_needs_tug(self):
        fh = CargoVehicle("Falcon Heavy", "USA", 63800, 145, 150, False, "Operational")
        tug = TransferStage("Chemical Kick Stage", 2000, 15000, 450, False)
        tm = TransferModel()
        result = tm.compute_delivery(fh, transfer_type="direct", transfer_stage=tug)
        assert result.mass_delivered_kg > 0
        assert result.mass_delivered_kg < 63800

    def test_leo_only_without_tug_raises(self):
        fh = CargoVehicle("Falcon Heavy", "USA", 63800, 145, 150, False, "Operational")
        tm = TransferModel()
        with pytest.raises(ValueError, match="requires a transfer stage"):
            tm.compute_delivery(fh, transfer_type="direct", transfer_stage=None)

    def test_sep_tug_delivers_more_than_chemical(self):
        fh = CargoVehicle("Falcon Heavy", "USA", 63800, 145, 150, False, "Operational")
        chem = TransferStage("Chemical Kick Stage", 2000, 15000, 450, False)
        sep = TransferStage("SEP Tug", 5000, 2000, 3000, True)
        tm = TransferModel()
        result_chem = tm.compute_delivery(fh, transfer_type="direct", transfer_stage=chem)
        result_sep = tm.compute_delivery(fh, transfer_type="low_energy", transfer_stage=sep)
        assert result_sep.mass_delivered_kg > result_chem.mass_delivered_kg
