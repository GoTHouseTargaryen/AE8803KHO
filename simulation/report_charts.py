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
    """Broken horizontal bar Gantt chart of assembly actions."""
    fig, ax = plt.subplots(figsize=(3.5, max(2.0, len(timeline) * 0.12 + 1.0)))

    yticks, ylabels = [], []
    y = 0
    for entry in timeline:
        period = entry["period"]
        for action in entry.get("actions", []):
            color = "#AAAAAA"
            label = action[:40]
            for key, col in _ACTION_COLORS.items():
                if action.startswith(key):
                    color = col
                    label = action.split(":", 1)[1][:35] if ":" in action else action
                    break
            ax.barh(y, 1, left=period, height=0.6, color=color, alpha=0.85)
            yticks.append(y)
            ylabels.append(label)
            y += 1

    if not yticks:
        ax.text(0.5, 0.5, "No actions", transform=ax.transAxes, ha="center")
    else:
        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels, fontsize=6)

    ax.set_xlabel("Period")
    ax.set_title("Assembly Timeline", fontsize=9)

    legend_patches = [mpatches.Patch(color=c, label=k)
                      for k, c in _ACTION_COLORS.items()]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=6)

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
    """Horizontal bar chart of cost by vehicle."""
    data = _parse_timeline(timeline)
    vehicle_counts: dict[str, int] = defaultdict(int)
    for launches in data["launches"].values():
        for v in launches:
            vehicle_counts[v] += 1
    for crew in data["crew"].values():
        for v in crew:
            vehicle_counts[v] += 1

    if not vehicle_counts:
        vehicle_counts["No launches"] = 1

    vehicles = list(vehicle_counts.keys())
    counts = [vehicle_counts[v] for v in vehicles]
    total_count = sum(counts)
    costs = [
        (c / total_count) * total_cost_million if total_count > 0 else 0
        for c in counts
    ]

    fig, ax = plt.subplots(figsize=(3.5, max(1.8, len(vehicles) * 0.4 + 0.6)))
    bars = ax.barh(vehicles, costs, color="#2196F3", alpha=0.85)
    ax.set_xlabel("Cost (USD M)")
    ax.set_title("Cost Breakdown by Vehicle", fontsize=9)
    for bar, cost in zip(bars, costs):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{cost:.0f}M USD", va="center", fontsize=7)
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
        ax.annotate(label[:15], (launches[i], periods[i]),
                    fontsize=6, xytext=(4, 2), textcoords="offset points")

    ax.set_xlabel("Total Launches")
    ax.set_ylabel("Total Periods")
    ax.set_title("Pareto Frontier", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, backend="pgf")
    plt.close(fig)
