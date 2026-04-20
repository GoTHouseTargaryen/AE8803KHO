# simulation/app.py
from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage
from simulation.parametric import generate_spacecraft
from simulation.proximity import ProximityModel
from simulation.transfer import TransferModel
from simulation.solver.objectives import ObjectiveWeights
from simulation.solver.dp_solver import DPSolver, SolverConfig
from simulation.report_builder import build_report

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> list[dict]:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    @app.route("/api/catalog/cargo-vehicles")
    def get_cargo_vehicles():
        return jsonify(_load_json("cargo_vehicles.json"))

    @app.route("/api/catalog/crew-vehicles")
    def get_crew_vehicles():
        return jsonify(_load_json("crew_vehicles.json"))

    @app.route("/api/catalog/transfer-stages")
    def get_transfer_stages():
        return jsonify(_load_json("transfer_stages.json"))

    @app.route("/api/catalog/modules")
    def get_modules():
        return jsonify(_load_json("module_catalog.json"))

    @app.route("/api/generate", methods=["POST"])
    def generate():
        body = request.get_json()
        dag = generate_spacecraft(
            length_km=body["length_km"],
            structure_type=body["structure_type"],
            propulsion_type=body["propulsion_type"],
            power_type=body["power_type"],
        )
        modules = [
            {
                "id": m.id,
                "type": m.type,
                "mass_kg": m.mass_kg,
                "assembly_hours": m.assembly_hours,
                "crew_required": m.crew_required,
                "category": m.category,
                "power_output_kw": m.power_output_kw,
                "isp": m.isp,
                "thrust_level": m.thrust_level,
                "required_power_system": m.required_power_system,
            }
            for m in dag.modules.values()
        ]
        dependencies = {
            mid: dag.get_prerequisites(mid) for mid in dag.modules
        }
        return jsonify({"modules": modules, "dependencies": dependencies})

    @app.route("/api/simulate", methods=["POST"])
    def simulate():
        body = request.get_json()

        sc = body["spacecraft"]
        dag = generate_spacecraft(
            length_km=sc["length_km"],
            structure_type=sc["structure_type"],
            propulsion_type=sc["propulsion_type"],
            power_type=sc["power_type"],
        )

        all_cargo = {v.name: v for v in CargoVehicle.default_catalog()}
        all_crew = {v.name: v for v in CrewVehicle.default_catalog()}
        all_stages = {s.name: s for s in TransferStage.default_catalog()}

        cargo_vehicles = [all_cargo[n] for n in body["cargo_vehicles"] if n in all_cargo]
        crew_vehicles  = [all_crew[n]  for n in body["crew_vehicles"]  if n in all_crew]
        transfer_stages = [all_stages[n] for n in body["transfer_stages"] if n in all_stages]

        w = body.get("weights", {})
        prox = body.get("proximity", {})

        config = SolverConfig(
            dag=dag,
            cargo_vehicles=cargo_vehicles,
            crew_vehicles=crew_vehicles,
            transfer_stages=transfer_stages,
            weights=ObjectiveWeights(
                w_launches=w.get("w_launches", 1.0),
                w_time=w.get("w_time", 1.0),
                w_cost=w.get("w_cost", 1.0),
            ),
            proximity=ProximityModel(
                alpha=prox.get("alpha", 0.1),
                beta=prox.get("beta", 1.5),
                base_capacity=prox.get("base_capacity", 2),
                max_capacity=prox.get("max_capacity", 10),
            ),
            transfer=TransferModel(),
            period_days=body.get("period_days", 7),
            beam_width=body.get("beam_width", 100),
            max_periods=body.get("max_periods", 200),
            max_eva_hours_per_session=body.get("max_eva_hours_per_session", 6),
            max_pairs_per_iva=body.get("max_pairs_per_iva", 2),
            robotic_time_penalty=body.get("robotic_time_penalty", 1.5),
        )

        solver = DPSolver(config)
        result = solver.solve()

        return jsonify({
            "total_launches": result.total_launches,
            "total_periods": result.total_periods,
            "total_cost_million": result.total_cost_million,
            "modules_completed": result.modules_completed,
            "cumulative_risk": result.cumulative_risk,
            "timeline": result.timeline,
        })

    @app.route("/api/pareto", methods=["POST"])
    def pareto():
        """Run the solver across a grid of weight combinations and return the Pareto frontier."""
        body = request.get_json()

        sc = body["spacecraft"]
        dag = generate_spacecraft(
            length_km=sc["length_km"],
            structure_type=sc["structure_type"],
            propulsion_type=sc["propulsion_type"],
            power_type=sc["power_type"],
        )

        all_cargo = {v.name: v for v in CargoVehicle.default_catalog()}
        all_crew = {v.name: v for v in CrewVehicle.default_catalog()}
        all_stages = {s.name: s for s in TransferStage.default_catalog()}

        cargo_vehicles = [all_cargo[n] for n in body["cargo_vehicles"] if n in all_cargo]
        crew_vehicles = [all_crew[n] for n in body["crew_vehicles"] if n in all_crew]
        transfer_stages = [all_stages[n] for n in body["transfer_stages"] if n in all_stages]

        prox = body.get("proximity", {})
        base_config_kwargs = dict(
            dag=dag,
            cargo_vehicles=cargo_vehicles,
            crew_vehicles=crew_vehicles,
            transfer_stages=transfer_stages,
            proximity=ProximityModel(
                alpha=prox.get("alpha", 0.1),
                beta=prox.get("beta", 1.5),
                base_capacity=prox.get("base_capacity", 2),
                max_capacity=prox.get("max_capacity", 10),
            ),
            transfer=TransferModel(),
            period_days=body.get("period_days", 7),
            beam_width=body.get("beam_width", 50),
            max_periods=body.get("max_periods", 200),
            max_eva_hours_per_session=body.get("max_eva_hours_per_session", 6),
            max_pairs_per_iva=body.get("max_pairs_per_iva", 2),
            robotic_time_penalty=body.get("robotic_time_penalty", 1.5),
        )

        # Grid: vary each weight from 0 to 2 in steps; normalise so sum > 0
        steps = body.get("pareto_steps", 3)
        weight_values = [i / (steps - 1) * 2.0 for i in range(steps)] if steps > 1 else [1.0]

        points = []
        seen: set[tuple] = set()
        for wl in weight_values:
            for wt in weight_values:
                for wc in weight_values:
                    if wl + wt + wc == 0:
                        continue
                    config = SolverConfig(
                        weights=ObjectiveWeights(w_launches=wl, w_time=wt, w_cost=wc),
                        **base_config_kwargs,
                    )
                    result = DPSolver(config).solve()
                    key = (result.total_launches, result.total_periods, round(result.total_cost_million, 1))
                    if key in seen:
                        continue
                    seen.add(key)
                    points.append({
                        "w_launches": wl,
                        "w_time": wt,
                        "w_cost": wc,
                        "total_launches": result.total_launches,
                        "total_periods": result.total_periods,
                        "total_cost_million": result.total_cost_million,
                        "modules_completed": result.modules_completed,
                    })

        # Filter to non-dominated points
        pareto = []
        for p in points:
            dominated = False
            for q in points:
                if (
                    q["total_launches"] <= p["total_launches"]
                    and q["total_periods"] <= p["total_periods"]
                    and q["total_cost_million"] <= p["total_cost_million"]
                    and q != p
                    and (
                        q["total_launches"] < p["total_launches"]
                        or q["total_periods"] < p["total_periods"]
                        or q["total_cost_million"] < p["total_cost_million"]
                    )
                ):
                    dominated = True
                    break
            if not dominated:
                pareto.append(p)

        return jsonify({"points": pareto, "all_points": points})

    @app.route("/api/report", methods=["POST"])
    def compile_report():
        body = request.get_json()
        runs = body.get("runs") if body else None

        if not runs:
            return jsonify({"error": "No runs provided. Tag at least one simulation run."}), 400

        try:
            pdf_bytes = build_report(runs)
        except FileNotFoundError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception as exc:
            import traceback
            return jsonify({"error": str(exc), "detail": traceback.format_exc()}), 500

        from flask import Response
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="report.pdf"'},
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
