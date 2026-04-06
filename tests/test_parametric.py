# tests/test_parametric.py
from simulation.parametric import generate_spacecraft
from simulation.models.modules import AssemblyDAG


class TestParametricGenerator:
    def test_generates_dag(self):
        dag = generate_spacecraft(
            length_km=2.0,
            structure_type="truss",
            propulsion_type="NEP",
            power_type="Fusion",
        )
        assert isinstance(dag, AssemblyDAG)
        assert dag.total_modules > 0

    def test_truss_count_scales_with_length(self):
        dag_1km = generate_spacecraft(length_km=1.0, structure_type="truss",
                                       propulsion_type="Chemical", power_type="Solar")
        dag_2km = generate_spacecraft(length_km=2.0, structure_type="truss",
                                       propulsion_type="Chemical", power_type="Solar")
        truss_1 = sum(1 for m in dag_1km.modules.values() if m.type == "Truss Section")
        truss_2 = sum(1 for m in dag_2km.modules.values() if m.type == "Truss Section")
        assert truss_2 > truss_1

    def test_nep_requires_fission_or_fusion(self):
        dag = generate_spacecraft(length_km=1.0, structure_type="truss",
                                   propulsion_type="NEP", power_type="Fission")
        nep_modules = [m for m in dag.modules.values() if "NEP" in m.type]
        assert len(nep_modules) > 0
        for nep in nep_modules:
            prereqs = dag.get_prerequisites(nep.id)
            has_power_prereq = any("fission" in p or "fusion" in p for p in prereqs)
            assert has_power_prereq

    def test_sep_requires_solar(self):
        dag = generate_spacecraft(length_km=1.0, structure_type="truss",
                                   propulsion_type="SEP", power_type="Solar")
        sep_modules = [m for m in dag.modules.values() if "SEP" in m.type]
        assert len(sep_modules) > 0
        for sep in sep_modules:
            prereqs = dag.get_prerequisites(sep.id)
            has_solar = any("solar" in p for p in prereqs)
            assert has_solar

    def test_has_docking_node(self):
        dag = generate_spacecraft(length_km=1.0, structure_type="truss",
                                   propulsion_type="Chemical", power_type="Solar")
        docking = [m for m in dag.modules.values() if "Docking" in m.type]
        assert len(docking) >= 1

    def test_topological_sort_valid(self):
        dag = generate_spacecraft(length_km=2.0, structure_type="truss",
                                   propulsion_type="NTP", power_type="Fission")
        order = dag.topological_sort()
        assert len(order) == dag.total_modules

    def test_module_count_reasonable(self):
        dag = generate_spacecraft(length_km=2.0, structure_type="truss",
                                   propulsion_type="Chemical", power_type="Solar")
        assert 20 <= dag.total_modules <= 60
