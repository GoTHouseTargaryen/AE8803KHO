import pytest
from simulation.models.modules import Module, AssemblyDAG


class TestModule:
    def test_create_module(self):
        m = Module(
            id="truss_1",
            type="Truss Section",
            mass_kg=5000,
            assembly_hours=48,
            crew_required=False,
            category="structural",
        )
        assert m.id == "truss_1"
        assert m.mass_kg == 5000
        assert m.crew_required is False

    def test_module_defaults(self):
        m = Module(
            id="hab_1",
            type="Habitat Block",
            mass_kg=20000,
            assembly_hours=120,
            crew_required=True,
            category="habitation",
        )
        assert m.power_output_kw == 0
        assert m.required_power_system is None
        assert m.isp is None

    def test_propulsion_module_with_power_requirement(self):
        m = Module(
            id="nep_1",
            type="Nuclear Electric (NEP)",
            mass_kg=30000,
            assembly_hours=160,
            crew_required=True,
            category="propulsion",
            isp=5000,
            thrust_level="Low",
            required_power_system="Fission or Fusion",
        )
        assert m.required_power_system == "Fission or Fusion"
        assert m.isp == 5000

    def test_power_module(self):
        m = Module(
            id="fission_1",
            type="Fission Reactor Unit",
            mass_kg=15000,
            assembly_hours=100,
            crew_required=True,
            category="power",
            power_output_kw=500,
        )
        assert m.power_output_kw == 500


class TestAssemblyDAG:
    def _make_modules(self):
        truss = Module(id="truss_1", type="Truss Section", mass_kg=5000,
                       assembly_hours=48, crew_required=False, category="structural")
        power = Module(id="solar_1", type="Solar Array Unit", mass_kg=6000,
                       assembly_hours=36, crew_required=False, category="power",
                       power_output_kw=100)
        hab = Module(id="hab_1", type="Habitat Block", mass_kg=20000,
                     assembly_hours=120, crew_required=True, category="habitation")
        return truss, power, hab

    def test_add_modules_and_dependencies(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        dag.add_module(power, prerequisites=["truss_1"])
        dag.add_module(hab, prerequisites=["truss_1"])
        assert dag.get_prerequisites("solar_1") == ["truss_1"]
        assert dag.get_prerequisites("truss_1") == []

    def test_available_modules(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        dag.add_module(power, prerequisites=["truss_1"])
        dag.add_module(hab, prerequisites=["truss_1"])

        built = set()
        available = dag.get_available(built)
        assert available == {"truss_1"}

        built = {"truss_1"}
        available = dag.get_available(built)
        assert available == {"solar_1", "hab_1"}

    def test_topological_order(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        dag.add_module(power, prerequisites=["truss_1"])
        dag.add_module(hab, prerequisites=["truss_1"])
        order = dag.topological_sort()
        assert order.index("truss_1") < order.index("solar_1")
        assert order.index("truss_1") < order.index("hab_1")

    def test_cycle_detection(self):
        m1 = Module(id="a", type="X", mass_kg=1, assembly_hours=1,
                    crew_required=False, category="structural")
        m2 = Module(id="b", type="X", mass_kg=1, assembly_hours=1,
                    crew_required=False, category="structural")
        dag = AssemblyDAG()
        dag.add_module(m1)
        dag.add_module(m2, prerequisites=["a"])
        # Manually inject a cycle
        dag.prerequisites["a"] = ["b"]
        with pytest.raises(ValueError, match="cycle"):
            dag.topological_sort()

    def test_total_modules(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        dag.add_module(power, prerequisites=["truss_1"])
        dag.add_module(hab, prerequisites=["truss_1"])
        assert dag.total_modules == 3

    def test_get_module(self):
        truss, power, hab = self._make_modules()
        dag = AssemblyDAG()
        dag.add_module(truss)
        assert dag.get_module("truss_1") is truss
