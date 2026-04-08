# simulation/report_builder.py
"""Orchestrates chart generation, Jinja2 rendering, and pdflatex compilation."""
from __future__ import annotations

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
)

REPORT_DIR = Path(__file__).parent.parent / "report"
TEMPLATE_PATH = REPORT_DIR / "sections" / "results.tex.j2"
GENERATED_DIR = REPORT_DIR / "generated"


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
        generate_pareto(runs, str(GENERATED_DIR / "pareto.pgf"))

    # Render results.tex from Jinja2 template
    render_results_tex(runs, str(REPORT_DIR / "sections" / "results.tex"))

    # Run pdflatex twice (for cross-references)
    pdf_path = REPORT_DIR / "report.pdf"
    log_path = REPORT_DIR / "report.log"

    for _ in range(2):
        proc = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "report.tex"],
            cwd=str(REPORT_DIR),
            capture_output=True,
            text=True,
            timeout=120,
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
