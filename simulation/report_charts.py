# simulation/report_charts.py
"""Matplotlib pgf chart generators for the AIAA report."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("pgf")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "font.family": "serif",
    "text.usetex": False,
    "pgf.rcfonts": False,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.figsize": (3.5, 2.2),
})

_ACTION_COLORS = {
    "launched": "#2196F3",
    "crew_launch": "#FF9800",
    "assembled": "#4CAF50",
    "wip": "#9C27B0",
}

# LaTeX special chars that break the pgf font-metrics subprocess even when text.usetex=False
_LATEX_SPECIAL = str.maketrans({
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "~": r"\textasciitilde ",
    "^": r"\textasciicircum ",
})


def _tex(text: str) -> str:
    """Escape LaTeX special characters in a string used as a chart label."""
    return text.translate(_LATEX_SPECIAL)


def _parse_timeline(timeline: list[dict]) -> dict:
    """Return period-indexed parsed action data."""
    data: dict = {
        "launches": defaultdict(list),
        "crew": defaultdict(list),
        "assembled": defaultdict(list),
        "wip": defaultdict(list),
        "crew_count": [],
        "vehicle_count": [],
        "modules_cumulative": [],
    }
    crew_onsite = 0
    modules_done = 0
    for entry in timeline:
        period = entry["period"]
        actions = entry.get("actions", [])
        for action in actions:
            if action.startswith("launched:"):
                parts = action.split(":", 2)
                vehicle = parts[1] if len(parts) > 1 else "unknown"
                data["launches"][period].append(vehicle)
            elif action.startswith("crew_launch:"):
                parts = action.split(":", 2)
                vehicle = parts[1] if len(parts) > 1 else "unknown"
                data["crew"][period].append(vehicle)
                crew_onsite = 5
            elif action.startswith("assembled:"):
                mod = action.split(":", 1)[1]
                data["assembled"][period].append(mod)
                modules_done += 1
            elif action.startswith("wip:"):
                mod = action.split(":")[1]
                data["wip"][period].append(mod)
        data["crew_count"].append(crew_onsite)
        data["vehicle_count"].append(
            len(data["launches"][period]) + (1 if crew_onsite > 0 else 0)
        )
        data["modules_cumulative"].append(modules_done)
        if crew_onsite > 0:
            crew_onsite = max(0, crew_onsite - 0)
    return data


def generate_gantt(timeline: list[dict], output_path: str) -> None:
    """Module-level Gantt chart: one row per module, capped to fit one page."""
    module_start: dict[str, int] = {}
    module_end: dict[str, int] = {}
    launch_events: list[tuple[int, str]] = []
    crew_events: list[tuple[int, str]] = []
    max_period = 0

    for entry in timeline:
        period = entry["period"]
        max_period = max(max_period, period)
        for action in entry.get("actions", []):
            if action.startswith("wip:"):
                mid = action.split(":")[1]
                module_start.setdefault(mid, period)
            elif action.startswith("assembled:"):
                mid = action.split(":", 1)[1]
                module_start.setdefault(mid, period)
                module_end[mid] = period
            elif action.startswith("launched:"):
                vehicle = action.split(":")[1] if action.count(":") >= 1 else "unknown"
                launch_events.append((period, vehicle))
            elif action.startswith("crew_launch:"):
                vehicle = action.split(":")[1] if action.count(":") >= 1 else "unknown"
                crew_events.append((period, vehicle))

    modules = sorted(module_start, key=lambda m: (module_start[m], m))

    if not modules:
        fig, ax = plt.subplots(figsize=(6.5, 2.0))
        ax.text(0.5, 0.5, "No assembly actions", transform=ax.transAxes, ha="center")
        fig.savefig(output_path, backend="pgf")
        plt.close(fig)
        return

    ROW_H = 0.35
    ROW_STEP = 0.55
    # Cap height so chart fits on one page (letter minus margins minus caption ≈ 7 in)
    fig_h = min(max(2.0, len(modules) * ROW_STEP + 1.2), 7.0)

    fig, ax = plt.subplots(figsize=(6.5, fig_h))

    for i, mid in enumerate(modules):
        y = i * ROW_STEP
        start = module_start[mid]
        end = module_end.get(mid, max_period)
        wip_dur = max(end - start, 1)
        # WIP bar (purple) followed by completion bar (green overlay)
        ax.barh(y, wip_dur, left=start, height=ROW_H,
                color="#9C27B0", alpha=0.55, linewidth=0)
        if mid in module_end:
            ax.barh(y, 1, left=end, height=ROW_H,
                    color="#4CAF50", alpha=0.9, linewidth=0)

    # Cargo and crew events as short vertical ticks in the top margin
    y_top = len(modules) * ROW_STEP
    for p, _ in launch_events:
        ax.plot([p + 0.5, p + 0.5], [y_top + 0.05, y_top + 0.35],
                color="#2196F3", linewidth=1.2, clip_on=False)
    for p, _ in crew_events:
        ax.plot([p + 0.5, p + 0.5], [y_top + 0.05, y_top + 0.35],
                color="#FF9800", linewidth=1.8, clip_on=False)

    yticks = [i * ROW_STEP for i in range(len(modules))]
    ylabels = [_tex(m[:20]) for m in modules]
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=5)
    ax.set_ylim(-ROW_STEP * 0.5, y_top + 0.5)
    ax.set_xlabel("Period", fontsize=8)
    ax.set_title("Assembly Timeline", fontsize=9)

    legend_patches = [
        mpatches.Patch(color="#9C27B0", alpha=0.7, label="WIP"),
        mpatches.Patch(color="#4CAF50", label="Assembled"),
        mpatches.Patch(color="#2196F3", label="Cargo launch"),
        mpatches.Patch(color="#FF9800", label="Crew launch"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=5, ncol=2)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_resources(timeline: list[dict], output_path: str) -> None:
    """Dual-axis line chart: crew count and vehicle count over time."""
    data = _parse_timeline(timeline)
    periods = list(range(len(timeline)))

    fig, ax1 = plt.subplots(figsize=(3.5, 2.2))
    ax2 = ax1.twinx()

    ax1.plot(periods, data["crew_count"], color="#FF9800", label="Crew on-site")
    ax2.plot(periods, data["vehicle_count"], color="#2196F3",
             linestyle="--", label="Vehicles in prox.")

    ax1.set_xlabel("Period")
    ax1.set_ylabel("Crew count", color="#FF9800", fontsize=8)
    ax2.set_ylabel("Vehicle count", color="#2196F3", fontsize=8)
    ax1.set_title("Resource Utilization", fontsize=9)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper left")

    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_cost_breakdown(
    timeline: list[dict],
    total_cost_million: float,
    output_path: str,
) -> None:
    """Two-panel horizontal bar chart: cargo launches (top) and crew launches (bottom).
    Costs are computed from the vehicle catalog (count × cost_per_launch), not
    proportionally from total_cost_million, so expensive vehicles appear correctly."""
    from simulation.models.vehicles import CargoVehicle, CrewVehicle

    cargo_price = {v.name: v.cost_per_launch_million for v in CargoVehicle.default_catalog()}
    crew_price  = {v.name: v.cost_per_launch_million for v in CrewVehicle.default_catalog()}

    data = _parse_timeline(timeline)

    cargo_counts: dict[str, int] = defaultdict(int)
    for launches in data["launches"].values():
        for v in launches:
            cargo_counts[v] += 1

    crew_counts: dict[str, int] = defaultdict(int)
    for crew in data["crew"].values():
        for v in crew:
            crew_counts[v] += 1

    def _build_panel(counts: dict[str, int], price_map: dict[str, float]):
        names  = list(counts.keys())
        costs  = [counts[n] * price_map.get(n, 0.0) for n in names]
        labels = [_tex(n) for n in names]
        return labels, costs

    cargo_labels, cargo_costs = _build_panel(cargo_counts, cargo_price)
    crew_labels,  crew_costs  = _build_panel(crew_counts,  crew_price)

    has_cargo = bool(cargo_labels)
    has_crew  = bool(crew_labels)
    n_panels  = (1 if has_cargo else 0) + (1 if has_crew else 0)
    if n_panels == 0:
        cargo_labels, cargo_costs = ["No launches"], [0.0]
        has_cargo, n_panels = True, 1

    panel_data = []
    if has_cargo:
        panel_data.append(("Launch Vehicles", cargo_labels, cargo_costs, "#2196F3"))
    if has_crew:
        panel_data.append(("Crew Vehicles", crew_labels, crew_costs, "#FF9800"))

    heights = [max(1.2, len(labels) * 0.38 + 0.5) for _, labels, __, ___ in panel_data]
    fig_h = sum(heights) + 0.4 * (n_panels - 1)
    fig, axes = plt.subplots(
        n_panels, 1,
        figsize=(3.5, fig_h),
        gridspec_kw={"height_ratios": heights} if n_panels > 1 else {},
        squeeze=False,
    )

    for ax, (title, labels, costs, color) in zip(axes[:, 0], panel_data):
        bars = ax.barh(labels, costs, color=color, alpha=0.85)
        ax.set_xlabel("Cost (USD M)")
        ax.set_title(title, fontsize=8, fontweight="bold")
        for bar, cost in zip(bars, costs):
            if cost > 0:
                ax.text(bar.get_width() + max(costs) * 0.02,
                        bar.get_y() + bar.get_height() / 2,
                        f"{cost:.0f}M", va="center", fontsize=6.5)
        x_max = max(costs) if costs else 1
        ax.set_xlim(0, x_max * 1.25)

    fig.suptitle("Cost Breakdown by Vehicle", fontsize=9, y=1.0)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_modules_over_time(
    timeline: list[dict],
    total_modules: int,
    output_path: str,
) -> None:
    """Step chart of cumulative modules completed over time."""
    data = _parse_timeline(timeline)
    periods = list(range(len(timeline)))
    cumulative = data["modules_cumulative"]

    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    ax.step(periods, cumulative, where="post", color="#4CAF50", linewidth=1.5)
    ax.axhline(total_modules, color="#F44336", linestyle=":", linewidth=1,
               label=f"Target ({total_modules})")
    ax.set_xlabel("Period")
    ax.set_ylabel("Modules completed")
    ax.set_title("Assembly Progress", fontsize=9)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_solution_space(
    all_points: list[dict],
    tagged_runs: list[dict],
    max_periods: int,
    output_path: str,
) -> None:
    """Objective-space scatter of all explored weight combinations with constraint overlay."""
    import numpy as np

    if not all_points:
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        ax.text(0.5, 0.5, "No solution space data", transform=ax.transAxes, ha="center")
        fig.savefig(output_path, backend="pgf")
        plt.close(fig)
        return

    launches = [p["total_launches"] for p in all_points]
    periods  = [p["total_periods"]   for p in all_points]
    costs    = [p["total_cost_million"] for p in all_points]

    # Identify Pareto-optimal points (non-dominated in all three objectives)
    is_pareto = []
    for i, p in enumerate(all_points):
        dominated = any(
            q["total_launches"] <= p["total_launches"]
            and q["total_periods"] <= p["total_periods"]
            and q["total_cost_million"] <= p["total_cost_million"]
            and (q["total_launches"] < p["total_launches"]
                 or q["total_periods"] < p["total_periods"]
                 or q["total_cost_million"] < p["total_cost_million"])
            for j, q in enumerate(all_points) if i != j
        )
        is_pareto.append(not dominated)

    # Empirical minimum feasible period (lead time + transit floor)
    min_feasible = min(periods) if periods else 0

    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    # Infeasible region: above max_periods constraint
    ymax_display = max(max(periods) * 1.15, max_periods * 1.05)
    ax.axhspan(max_periods, ymax_display, alpha=0.12, color="#F44336",
               label=f"$T > {max_periods}$ (infeasible)")

    # Lead-time floor: below minimum achievable duration
    if min_feasible > 0:
        ax.axhspan(0, min_feasible - 0.5, alpha=0.10, color="#FF9800",
                   label=f"Lead-time floor ($T < {min_feasible}$)")

    # Dominated points (small, faded)
    dom_l = [launches[i] for i, p in enumerate(is_pareto) if not p]
    dom_p = [periods[i]  for i, p in enumerate(is_pareto) if not p]
    dom_c = [costs[i]    for i, p in enumerate(is_pareto) if not p]
    if dom_l:
        ax.scatter(dom_l, dom_p, c=dom_c, cmap="YlOrRd",
                   s=18, alpha=0.4, edgecolors="none", zorder=2)

    # Pareto-optimal points (larger, outlined diamonds)
    par_l = [launches[i] for i, p in enumerate(is_pareto) if p]
    par_p = [periods[i]  for i, p in enumerate(is_pareto) if p]
    par_c = [costs[i]    for i, p in enumerate(is_pareto) if p]
    sc = None
    if par_l:
        sc = ax.scatter(par_l, par_p, c=par_c, cmap="YlOrRd",
                        s=55, edgecolors="k", linewidths=0.6,
                        marker="D", zorder=4, label="Pareto-optimal")
        # Connect Pareto frontier with a step line
        pareto_sorted = sorted(zip(par_l, par_p), key=lambda x: x[0])
        ax.step([pt[0] for pt in pareto_sorted],
                [pt[1] for pt in pareto_sorted],
                where="post", color="#333333", linewidth=0.8,
                linestyle="--", zorder=3, alpha=0.6)
    elif dom_l:
        # fallback colorbar source
        sc = ax.scatter(dom_l, dom_p, c=dom_c, cmap="YlOrRd",
                        s=18, alpha=0.0, edgecolors="none")

    if sc is not None:
        cbar = fig.colorbar(sc, ax=ax, label="Cost (USD M)")
        cbar.ax.tick_params(labelsize=6)

    # Tagged runs (red stars)
    for run in tagged_runs:
        rl = run["result"]["total_launches"]
        rp = run["result"]["total_periods"]
        ax.scatter([rl], [rp], s=120, marker="*", color="#D32F2F",
                   edgecolors="k", linewidths=0.5, zorder=6)
        ax.annotate(_tex(run["label"][:14]), (rl, rp),
                    fontsize=5, xytext=(4, 3), textcoords="offset points")

    ax.set_xlabel("Total launches", fontsize=8)
    ax.set_ylabel("Mission duration (periods)", fontsize=8)
    ax.set_title("Solution Space and Constraint Boundaries", fontsize=9)
    ax.set_ylim(bottom=0, top=ymax_display)
    ax.legend(fontsize=6, loc="upper right", framealpha=0.8)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)


def generate_pareto(runs: list[dict], output_path: str) -> None:
    """Scatter plot of Pareto frontier across multiple runs."""
    launches = [r["result"]["total_launches"] for r in runs]
    periods = [r["result"]["total_periods"] for r in runs]
    costs = [r["result"]["total_cost_million"] for r in runs]
    labels = [r["label"] for r in runs]

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    sc = ax.scatter(launches, periods, c=costs, cmap="YlOrRd",
                    s=60, edgecolors="k", linewidths=0.5, zorder=3)
    cbar = fig.colorbar(sc, ax=ax, label="Cost (USD M)")
    cbar.ax.tick_params(labelsize=7)

    for i, label in enumerate(labels):
        ax.annotate(_tex(label[:15]), (launches[i], periods[i]),
                    fontsize=6, xytext=(4, 2), textcoords="offset points")

    ax.set_xlabel("Total Launches")
    ax.set_ylabel("Total Periods")
    ax.set_title("Pareto Frontier", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)
