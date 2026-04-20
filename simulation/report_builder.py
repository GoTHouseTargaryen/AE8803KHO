# simulation/report_builder.py
"""Orchestrates chart generation, Jinja2 rendering, and pdflatex compilation."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from simulation.report_charts import (
    generate_gantt,
    generate_resources,
    generate_cost_breakdown,
    generate_modules_over_time,
    generate_pareto,
    generate_solution_space,
)

REPORT_DIR = Path(__file__).parent.parent / "report"
TEMPLATE_PATH = REPORT_DIR / "sections" / "results.tex.j2"
MD_TEMPLATE_PATH = REPORT_DIR / "sections" / "results.md.j2"
GENERATED_DIR = REPORT_DIR / "generated"


def _fix_pgf_png_paths(pgf_path: Path) -> None:
    """Prefix bare PNG filenames in a pgf with 'generated/' so pdflatex (running
    from report/) can resolve the companion raster images written by matplotlib."""
    text = pgf_path.read_text(encoding="utf-8")
    fixed = re.sub(
        r'\{([^/{}\s]+\.png)\}',
        lambda m: "{generated/" + m.group(1) + "}",
        text,
    )
    if fixed != text:
        pgf_path.write_text(fixed, encoding="utf-8")


def render_results_tex(runs: list[dict], output_path: str) -> None:
    """Render the results.tex Jinja2 template with the given run data."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_PATH.parent)),
        variable_start_string=r"{{",
        variable_end_string=r"}}",
        block_start_string=r"{%",
        block_end_string=r"%}",
        comment_start_string=r"{#",
        comment_end_string=r"#}",
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template("results.tex.j2")
    rendered = template.render(runs=runs)
    Path(output_path).write_text(rendered, encoding="utf-8")


def _sweep_solution_space(run: dict) -> list[dict]:
    """Lightweight 3×3 weight sweep to populate the solution-space chart."""
    from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage
    from simulation.parametric import generate_spacecraft
    from simulation.proximity import ProximityModel
    from simulation.transfer import TransferModel
    from simulation.solver.objectives import ObjectiveWeights
    from simulation.solver.dp_solver import DPSolver, SolverConfig

    sc = run.get("config", {}).get("spacecraft", {})
    cfg = run.get("config", {})

    try:
        dag = generate_spacecraft(
            length_km=sc.get("length_km", 1.0),
            structure_type=sc.get("structure_type", "truss"),
            propulsion_type=sc.get("propulsion_type", "Chemical"),
            power_type=sc.get("power_type", "Solar"),
        )
    except Exception:
        return []

    all_cargo  = {v.name: v for v in CargoVehicle.default_catalog()}
    all_crew   = {v.name: v for v in CrewVehicle.default_catalog()}
    all_stages = {s.name: s for s in TransferStage.default_catalog()}

    cargo_names  = cfg.get("cargo_vehicles",  list(all_cargo.keys()))
    crew_names   = cfg.get("crew_vehicles",   list(all_crew.keys()))
    stage_names  = cfg.get("transfer_stages", list(all_stages.keys()))

    cargo_vehicles  = [all_cargo[n]  for n in cargo_names  if n in all_cargo]  or list(all_cargo.values())[:3]
    crew_vehicles   = [all_crew[n]   for n in crew_names   if n in all_crew]   or list(all_crew.values())[:2]
    transfer_stages = [all_stages[n] for n in stage_names  if n in all_stages] or list(all_stages.values())[:1]

    base_kwargs: dict = dict(
        dag=dag,
        cargo_vehicles=cargo_vehicles,
        crew_vehicles=crew_vehicles,
        transfer_stages=transfer_stages,
        proximity=ProximityModel(alpha=0.1, beta=1.5, base_capacity=2, max_capacity=10),
        transfer=TransferModel(),
        period_days=cfg.get("period_days", 7),
        beam_width=30,
        max_periods=cfg.get("max_periods", 200),
    )

    points: list[dict] = []
    seen: set[tuple] = set()
    for wl in [0.0, 1.0, 2.0]:
        for wt in [0.0, 1.0, 2.0]:
            for wc in [0.0, 1.0, 2.0]:
                if wl + wt + wc == 0:
                    continue
                try:
                    config = SolverConfig(
                        weights=ObjectiveWeights(w_launches=wl, w_time=wt, w_cost=wc),
                        **base_kwargs,
                    )
                    result = DPSolver(config).solve()
                    key = (result.total_launches, result.total_periods,
                           round(result.total_cost_million, 0))
                    if key not in seen:
                        seen.add(key)
                        points.append({
                            "total_launches": result.total_launches,
                            "total_periods": result.total_periods,
                            "total_cost_million": result.total_cost_million,
                            "w_launches": wl, "w_time": wt, "w_cost": wc,
                        })
                except Exception:
                    continue
    return points


def build_markdown_report(runs: list[dict]) -> str:
    """Render the results Markdown template and return the Markdown string."""
    env = Environment(
        loader=FileSystemLoader(str(MD_TEMPLATE_PATH.parent)),
        variable_start_string=r"{{",
        variable_end_string=r"}}",
        block_start_string=r"{%",
        block_end_string=r"%}",
        comment_start_string=r"{#",
        comment_end_string=r"#}",
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template("results.md.j2")
    return template.render(runs=runs)


def build_report(runs: list[dict]) -> bytes:
    """
    Full pipeline: generate pgf charts, render results.tex, run pdflatex twice.
    Returns the compiled PDF as bytes.
    Raises RuntimeError on pdflatex failure with last 50 log lines.
    Raises FileNotFoundError if pdflatex is not on PATH.
    """
    if shutil.which("pdflatex") is None:
        raise FileNotFoundError(
            "pdflatex not found on PATH. "
            "Install MiKTeX (https://miktex.org/) or TeX Live."
        )

    # Ensure generated/ directory exists and clear stale pgf files
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for old in GENERATED_DIR.glob("*.pgf"):
        old.unlink()

    # Generate per-run charts
    for i, run in enumerate(runs):
        timeline = run["result"].get("timeline", [])
        total_cost = run["result"].get("total_cost_million", 0.0)
        total_modules = run["result"].get("modules_completed", 0)

        generate_gantt(timeline, str(GENERATED_DIR / f"run_{i}_gantt.pgf"))
        generate_resources(timeline, str(GENERATED_DIR / f"run_{i}_resources.pgf"))
        generate_cost_breakdown(timeline, total_cost,
                                str(GENERATED_DIR / f"run_{i}_cost.pgf"))
        generate_modules_over_time(timeline, total_modules,
                                   str(GENERATED_DIR / f"run_{i}_modules.pgf"))

    # Generate Pareto chart if multiple runs
    if len(runs) >= 2:
        pareto_pgf = GENERATED_DIR / "pareto.pgf"
        generate_pareto(runs, str(pareto_pgf))
        _fix_pgf_png_paths(pareto_pgf)

    # Generate solution-space chart (sweep weight combinations for each run)
    space_points: list[dict] = []
    for run in runs:
        space_points.extend(_sweep_solution_space(run))
    max_periods_cfg = max(
        (run.get("config", {}).get("max_periods", 200) for run in runs), default=200
    )
    sol_pgf = GENERATED_DIR / "solution_space.pgf"
    generate_solution_space(space_points, runs, max_periods_cfg, str(sol_pgf))
    _fix_pgf_png_paths(sol_pgf)

    # Render results.tex from Jinja2 template
    render_results_tex(runs, str(REPORT_DIR / "sections" / "results.tex"))

    # Run pdflatex -> bibtex -> pdflatex -> pdflatex (resolves citations + refs)
    pdf_path = REPORT_DIR / "report.pdf"
    log_path = REPORT_DIR / "report.log"

    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "report.tex"],
        cwd=str(REPORT_DIR), capture_output=True, text=True, timeout=120,
    )
    if shutil.which("bibtex") is not None:
        subprocess.run(
            ["bibtex", "report"],
            cwd=str(REPORT_DIR), capture_output=True, text=True, timeout=60,
        )
    for _ in range(2):
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "report.tex"],
            cwd=str(REPORT_DIR), capture_output=True, text=True, timeout=120,
        )

    if not pdf_path.exists():
        log_tail = ""
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            log_tail = "\n".join(lines[-50:])
        raise RuntimeError(
            f"pdflatex failed to produce report.pdf.\n\nLast 50 log lines:\n{log_tail}"
        )

    return pdf_path.read_bytes()
