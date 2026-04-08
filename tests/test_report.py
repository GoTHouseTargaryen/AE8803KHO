import pytest
from pathlib import Path
import tempfile

from simulation.report_charts import (
    generate_gantt,
    generate_resources,
    generate_cost_breakdown,
    generate_modules_over_time,
    generate_pareto,
)

SAMPLE_TIMELINE = [
    {"period": 0, "actions": ["launched:Starship:truss_section_0,truss_section_1"]},
    {"period": 1, "actions": []},
    {"period": 2, "actions": ["crew_launch:Crew Dragon:5"]},
    {"period": 3, "actions": ["assembled:truss_section_0"]},
    {"period": 4, "actions": ["assembled:truss_section_1", "wip:habitat_block_0:40.0h_remaining"]},
    {"period": 5, "actions": ["assembled:habitat_block_0"]},
]

SAMPLE_RESULT = {
    "total_launches": 2,
    "total_periods": 6,
    "total_cost_million": 350.0,
    "modules_completed": 3,
    "cumulative_risk": 0.0012,
    "timeline": SAMPLE_TIMELINE,
}

SAMPLE_RUN = {
    "label": "Test Run",
    "config": {
        "spacecraft": {"length_km": 0.5, "propulsion_type": "Chemical", "power_type": "Solar"},
        "cargo_vehicles": ["Starship"],
        "crew_vehicles": ["Crew Dragon"],
        "weights": {"w_launches": 1.0, "w_time": 1.0, "w_cost": 1.0},
    },
    "result": SAMPLE_RESULT,
}


class TestChartGeneration:
    def test_generate_gantt_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "gantt.pgf"
            generate_gantt(SAMPLE_TIMELINE, str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_generate_resources_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "resources.pgf"
            generate_resources(SAMPLE_TIMELINE, str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_generate_cost_breakdown_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "cost.pgf"
            generate_cost_breakdown(SAMPLE_TIMELINE, SAMPLE_RESULT["total_cost_million"], str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_generate_modules_over_time_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "modules.pgf"
            generate_modules_over_time(SAMPLE_TIMELINE, SAMPLE_RESULT["modules_completed"], str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_generate_pareto_creates_pgf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "pareto.pgf"
            runs = [SAMPLE_RUN, {**SAMPLE_RUN, "label": "Run 2",
                                  "result": {**SAMPLE_RESULT, "total_launches": 4,
                                             "total_cost_million": 200.0}}]
            generate_pareto(runs, str(out))
            assert out.exists()
            assert out.stat().st_size > 0

    def test_gantt_empty_timeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "gantt.pgf"
            generate_gantt([], str(out))
            assert out.exists()


from simulation.report_builder import render_results_tex, build_report


class TestReportBuilder:
    def test_render_results_tex_single_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "results.tex"
            render_results_tex([SAMPLE_RUN], str(out))
            assert out.exists()
            content = out.read_text()
            assert "Test Run" in content
            assert "Total Launches" in content
            assert r"\section{Results" in content

    def test_render_results_tex_two_runs_has_pareto(self):
        run2 = {**SAMPLE_RUN, "label": "Run 2",
                "result": {**SAMPLE_RESULT, "total_launches": 5}}
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "results.tex"
            render_results_tex([SAMPLE_RUN, run2], str(out))
            content = out.read_text()
            assert "Pareto" in content
            assert "Multi-Scenario" in content

    def test_render_results_tex_escapes_underscores(self):
        run = {**SAMPLE_RUN, "label": "My_Test_Run"}
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "results.tex"
            render_results_tex([run], str(out))
            content = out.read_text()
            assert r"My\_Test\_Run" in content or "My" in content


from unittest.mock import patch

from simulation.app import create_app as create_flask_app


class TestReportEndpoint:
    @pytest.fixture
    def client(self):
        app = create_flask_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_report_endpoint_no_runs_returns_400(self, client):
        resp = client.post(
            "/api/report",
            json={"runs": []},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_report_endpoint_missing_runs_key_returns_400(self, client):
        resp = client.post(
            "/api/report",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestBuildReportPipeline:
    def test_build_report_raises_if_no_pdflatex(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(FileNotFoundError, match="pdflatex"):
                build_report([SAMPLE_RUN])

    def test_render_results_and_charts_without_pdflatex(self):
        """Verify chart generation + template rendering succeed independently of pdflatex."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gantt_out = Path(tmpdir) / "gantt.pgf"
            generate_gantt(SAMPLE_TIMELINE, str(gantt_out))
            assert gantt_out.exists()

            results_out = Path(tmpdir) / "results.tex"
            render_results_tex([SAMPLE_RUN], str(results_out))
            content = results_out.read_text()
            assert "Test Run" in content
            assert r"\section{Results" in content
