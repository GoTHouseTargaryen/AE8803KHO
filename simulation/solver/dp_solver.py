# simulation/solver/dp_solver.py
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from simulation.models.modules import AssemblyDAG
from simulation.models.vehicles import CargoVehicle, CrewVehicle, TransferStage
from simulation.models.crew import CrewState
from simulation.models.state import SimState, DockedCrewVehicle, CargoInTransit
from simulation.proximity import ProximityModel
from simulation.transfer import TransferModel
from simulation.solver.objectives import ObjectiveWeights, compute_cost

# Turnaround time (periods) before the same cargo vehicle can launch again
DEFAULT_PAD_TURNAROUND_PERIODS = 2


@dataclass
class SolverConfig:
    dag: AssemblyDAG
    cargo_vehicles: list[CargoVehicle]
    crew_vehicles: list[CrewVehicle]
    transfer_stages: list[TransferStage]
    weights: ObjectiveWeights
    proximity: ProximityModel
    transfer: TransferModel
    period_days: int = 7
    beam_width: int = 100
    max_periods: int = 200
    max_eva_hours_per_session: float = 6
    max_pairs_per_iva: int = 2
    robotic_time_penalty: float = 1.5
    duty_cycle: float = 0.6
    pad_turnaround_periods: int = DEFAULT_PAD_TURNAROUND_PERIODS


@dataclass
class SolverResult:
    total_launches: int
    total_periods: int
    total_cost_million: float
    modules_completed: int
    cumulative_risk: float
    timeline: list[dict[str, Any]]
    final_state: SimState


# Work-in-progress: module_id -> remaining assembly hours
_WIP = dict[str, float]

# last_launch_period: vehicle_name -> last period it was used
_LastLaunch = dict[str, int]

# Internal beam entry: SimState, modules delivered to site, WIP, last-launch map, timeline
_BeamEntry = tuple[SimState, frozenset[str], _WIP, _LastLaunch, list[dict]]


class DPSolver:
    def __init__(self, config: SolverConfig) -> None:
        self.config = config
        self.dag = config.dag
        self.total_modules = config.dag.total_modules

        # Build lookup of lead times and first-flight premiums keyed by vehicle name
        self._cargo_lead: dict[str, int] = {
            cv.name: cv.lead_time_periods for cv in config.cargo_vehicles
        }
        self._cargo_premium: dict[str, float] = {
            cv.name: cv.first_flight_cost_premium for cv in config.cargo_vehicles
        }
        self._crew_lead: dict[str, int] = {
            cv.name: cv.lead_time_periods for cv in config.crew_vehicles
        }
        self._crew_premium: dict[str, float] = {
            cv.name: cv.first_flight_cost_premium for cv in config.crew_vehicles
        }

        # Precompute best delivery option for each cargo vehicle
        self._delivery_cache: dict[str, tuple[float, int, float]] = {}
        for cv in config.cargo_vehicles:
            best_mass = 0.0
            best_transit = 999
            best_cost = cv.cost_per_launch_million
            for transfer_type in ["direct", "low_energy"]:
                stages = [None] if cv.l4_direct else config.transfer_stages
                for stage in stages:
                    try:
                        result = config.transfer.compute_delivery(cv, transfer_type, stage)
                        if result.mass_delivered_kg > best_mass:
                            best_mass = result.mass_delivered_kg
                            best_transit = result.transit_days
                            best_cost = result.cost_million
                    except ValueError:
                        continue
            if best_mass > 0:
                transit_periods = math.ceil(best_transit / config.period_days)
                self._delivery_cache[cv.name] = (best_mass, transit_periods, best_cost)

        # Crew vehicle delivery cache (transit periods for LEO-only crew vehicles via best stage)
        self._crew_transit_cache: dict[str, int] = {}
        for cv in config.crew_vehicles:
            if cv.l4_direct:
                self._crew_transit_cache[cv.name] = math.ceil(60 / config.period_days)
            else:
                # Use a transfer stage for crew transit — pick best mass-capable stage
                best_t = math.ceil(120 / config.period_days)
                for stage in config.transfer_stages:
                    try:
                        # Treat crew vehicle like a cargo vehicle for transit calculation
                        fake_cv = CargoVehicle(
                            cv.name, cv.nation, cv.mass_kg, 50,
                            cv.cost_per_launch_million, False, "crew"
                        )
                        res = config.transfer.compute_delivery(fake_cv, "direct", stage)
                        if res.mass_delivered_kg > 0:
                            best_t = math.ceil(res.transit_days / config.period_days)
                            break
                    except ValueError:
                        continue
                self._crew_transit_cache[cv.name] = best_t

    def _progress_score(
        self, state: SimState, delivered: frozenset[str], wip: _WIP
    ) -> float:
        """Higher is better: measures overall progress toward completion."""
        built = len(state.modules_built)
        at_site = delivered - state.modules_built
        n_delivered = len(at_site)
        n_in_transit = sum(len(c.module_ids) for c in state.cargo_in_transit)
        has_crew = 1.0 if state.total_crew > 0 else 0.0
        wip_progress = len(wip) * 0.5
        # Extra bonus when crew is on-site and there are modules ready to assemble
        ready_to_build = len(self.dag.get_available(state.modules_built) & at_site)
        crew_utility = has_crew * (5.0 + ready_to_build * 3.0)
        return (
            built * 10.0
            + n_delivered * 3.0
            + n_in_transit * 1.0
            + crew_utility
            + wip_progress
        )

    def _effective_progress(
        self, state: SimState, delivered: frozenset[str], wip: _WIP
    ) -> int:
        """Progress metric: built + delivered + in-transit + weighted crew coverage.

        Crew coverage = total periods-remaining across all docked vehicles, so a
        state with a freshly-launched crew (high periods_remaining) is NOT dominated
        by a state with an expiring crew (periods_remaining=1).
        """
        built = len(state.modules_built)
        at_site = len(delivered - state.modules_built)
        in_transit = sum(len(c.module_ids) for c in state.cargo_in_transit)
        crew_coverage = sum(cv.periods_remaining for cv in state.crew_vehicles)
        return built * 3 + at_site * 2 + in_transit + crew_coverage

    def _is_dominated(
        self,
        a_state: SimState, a_delivered: frozenset[str], a_wip: _WIP,
        b_state: SimState, b_delivered: frozenset[str], b_wip: _WIP,
    ) -> bool:
        """Return True if b is dominated by a across all objectives including pipeline progress."""
        a_prog = self._effective_progress(a_state, a_delivered, a_wip)
        b_prog = self._effective_progress(b_state, b_delivered, b_wip)
        return (
            a_prog >= b_prog
            and a_state.total_launches <= b_state.total_launches
            and a_state.period <= b_state.period
            and a_state.total_cost_million <= b_state.total_cost_million
            and (
                a_prog > b_prog
                or a_state.total_launches < b_state.total_launches
                or a_state.period < b_state.period
                or a_state.total_cost_million < b_state.total_cost_million
            )
        )

    def _prune_dominated(
        self, beam: list[tuple[SimState, frozenset[str], _WIP, _LastLaunch, list[dict], float]]
    ) -> list[tuple[SimState, frozenset[str], _WIP, _LastLaunch, list[dict], float]]:
        """Remove beam entries dominated by any other entry."""
        kept = []
        for i, entry_i in enumerate(beam):
            s_i, d_i, w_i = entry_i[0], entry_i[1], entry_i[2]
            dominated = False
            for j, entry_j in enumerate(beam):
                if i == j:
                    continue
                s_j, d_j, w_j = entry_j[0], entry_j[1], entry_j[2]
                if self._is_dominated(s_j, d_j, w_j, s_i, d_i, w_i):
                    dominated = True
                    break
            if not dominated:
                kept.append(entry_i)
        return kept

    def solve(self) -> SolverResult:
        initial = SimState.initial()
        beam: list[_BeamEntry] = [(initial, frozenset(), {}, {}, [])]

        for period in range(self.config.max_periods):
            if not beam:
                break

            # Check if any beam entry is complete
            for state, delivered, wip, last_launch, timeline in beam:
                if len(state.modules_built) == self.total_modules:
                    return self._make_result(state, timeline)

            next_beam: list[
                tuple[SimState, frozenset[str], _WIP, _LastLaunch, list[dict], float]
            ] = []

            for state, delivered, wip, last_launch, timeline in beam:
                successors = self._expand(state, delivered, wip, last_launch, period)
                for new_state, new_delivered, new_wip, new_last_launch, actions in successors:
                    cost = compute_cost(
                        self.config.weights,
                        new_state.total_launches,
                        new_state.period,
                        new_state.total_cost_million,
                        max_launches=self.total_modules * 2,
                        max_periods=self.config.max_periods,
                        max_cost_million=self.total_modules * 2000,
                    )
                    new_timeline = timeline + [
                        {"period": period, "actions": actions}
                    ]
                    next_beam.append(
                        (new_state, new_delivered, new_wip, new_last_launch, new_timeline, cost)
                    )

            # Sort: higher progress first, then lower cost to break ties
            next_beam.sort(
                key=lambda x: (
                    -self._progress_score(x[0], x[1], x[2]),
                    x[5],
                )
            )
            beam = [
                (s, d, w, ll, t)
                for s, d, w, ll, t, _ in next_beam[: self.config.beam_width]
            ]

        if beam:
            best_state, _, _, _, best_timeline = beam[0]
            return self._make_result(best_state, best_timeline)

        return self._make_result(initial, [])

    def _expand(
        self,
        state: SimState,
        delivered: frozenset[str],
        wip: _WIP,
        last_launch: _LastLaunch,
        period: int,
    ) -> list[tuple[SimState, frozenset[str], _WIP, _LastLaunch, list[str]]]:
        successors: list[tuple[SimState, frozenset[str], _WIP, _LastLaunch, list[str]]] = []

        # --- Process cargo arrivals ---
        new_delivered = set(delivered)
        remaining_transit: list[CargoInTransit] = []
        arriving_this_period = 0  # for proximity counting
        for cargo in state.cargo_in_transit:
            if cargo.arrival_period <= period:
                new_delivered.update(cargo.module_ids)
                arriving_this_period += 1
            else:
                remaining_transit.append(cargo)
        delivered_fs = frozenset(new_delivered)

        # --- Update crew rotations ---
        active_crew: list[DockedCrewVehicle] = []
        for cv in state.crew_vehicles:
            if cv.periods_remaining > 1:
                active_crew.append(
                    DockedCrewVehicle(
                        cv.vehicle_name, cv.crew_onboard, cv.periods_remaining - 1
                    )
                )

        # --- Compute assembly capacity ---
        total_crew = sum(cv.crew_onboard for cv in active_crew)
        progress = state.build_progress(self.total_modules)

        # Proximity: crew vehicles + arriving cargo vehicles count
        n_prox = len(active_crew) + arriving_this_period
        penalty = self.config.proximity.penalty(max(1, n_prox), progress)

        # Modules available per DAG and delivered to site
        available = self.dag.get_available(state.modules_built)
        buildable = available & delivered_fs

        crew_state_obj = CrewState(
            total_crew=total_crew,
            max_pairs_per_iva=self.config.max_pairs_per_iva,
            max_eva_hours_per_session=self.config.max_eva_hours_per_session,
            eva_days_per_period=self.config.period_days,
            n_robotic_arms=sum(
                1 for m in state.modules_built if "robotic_arm" in m
            ),
            hours_per_period=self.config.period_days * 24,
            robotic_time_penalty=self.config.robotic_time_penalty,
            duty_cycle=self.config.duty_cycle,
        )

        crew_hours = crew_state_obj.eva_hours_per_period / penalty
        robotic_hours = crew_state_obj.robotic_hours_per_period / penalty

        # --- Greedy assembly with partial-build (WIP) support ---
        newly_built: set[str] = set()
        new_wip: _WIP = dict(wip)  # copy current WIP
        remaining_crew_hours = crew_hours
        remaining_robotic_hours = robotic_hours
        actions: list[str] = []

        # First, continue work on WIP modules (they already passed DAG + delivery checks)
        completed_wip: list[str] = []
        for mid in sorted(new_wip.keys()):
            hours_left = new_wip[mid]
            mod = self.dag.get_module(mid)
            if mod.crew_required:
                applied = min(hours_left, remaining_crew_hours)
                remaining_crew_hours -= applied
            else:
                applied_robotic = min(hours_left, remaining_robotic_hours)
                remaining_robotic_hours -= applied_robotic
                applied = applied_robotic
                # Fall back to crew hours with penalty for remaining
                if applied < hours_left:
                    crew_equivalent = (hours_left - applied) / self.config.robotic_time_penalty
                    crew_applied = min(crew_equivalent, remaining_crew_hours)
                    remaining_crew_hours -= crew_applied
                    applied += crew_applied * self.config.robotic_time_penalty

            new_wip[mid] = hours_left - applied
            if new_wip[mid] <= 0.01:  # effectively complete
                completed_wip.append(mid)
                newly_built.add(mid)
                actions.append(f"assembled:{mid}")

        for mid in completed_wip:
            del new_wip[mid]

        # Then, start new modules from buildable set (not already in WIP or just completed)
        for mid in sorted(buildable):
            if mid in newly_built or mid in new_wip:
                continue
            mod = self.dag.get_module(mid)
            hours_needed = mod.assembly_hours

            if mod.crew_required:
                if remaining_crew_hours > 0:
                    applied = min(hours_needed, remaining_crew_hours)
                    remaining_crew_hours -= applied
                    hours_left = hours_needed - applied
                    if hours_left <= 0.01:
                        newly_built.add(mid)
                        actions.append(f"assembled:{mid}")
                    else:
                        new_wip[mid] = hours_left
                        actions.append(f"wip:{mid}:{hours_left:.1f}h_remaining")
            else:
                applied = 0.0
                # Try robotic first
                if remaining_robotic_hours > 0:
                    robotic_applied = min(hours_needed, remaining_robotic_hours)
                    remaining_robotic_hours -= robotic_applied
                    applied += robotic_applied

                # Fall back to crew with penalty
                if applied < hours_needed and remaining_crew_hours > 0:
                    remaining_raw = hours_needed - applied
                    crew_equivalent = remaining_raw / self.config.robotic_time_penalty
                    crew_applied = min(crew_equivalent, remaining_crew_hours)
                    remaining_crew_hours -= crew_applied
                    applied += crew_applied * self.config.robotic_time_penalty

                hours_left = hours_needed - applied
                if hours_left <= 0.01:
                    newly_built.add(mid)
                    actions.append(f"assembled:{mid}")
                elif applied > 0:
                    new_wip[mid] = hours_left
                    actions.append(f"wip:{mid}:{hours_left:.1f}h_remaining")

        new_modules_built = state.modules_built | frozenset(newly_built)

        # --- Tug fleet management ---
        # Reusable tugs that have completed return transit come back into the pool
        new_tugs = state.tugs_available
        # (Tug return tracking via tugs_available is already in state — preserved as-is for now)

        # --- Risk accumulation ---
        risk = self.config.proximity.collision_risk(n_prox, self.config.period_days)

        # --- Base state (no new launches) ---
        base_state = SimState(
            modules_built=new_modules_built,
            crew_vehicles=active_crew,
            cargo_in_transit=remaining_transit,
            cargo_at_site=state.cargo_at_site,
            tugs_available=new_tugs,
            period=period + 1,
            total_launches=state.total_launches,
            total_cost_million=state.total_cost_million,
            cumulative_risk=state.cumulative_risk + risk,
        )
        successors.append((base_state, delivered_fs, new_wip, last_launch, actions))

        # --- Determine modules that still need to be launched ---
        all_module_ids = set(self.dag.modules.keys())
        modules_not_delivered = all_module_ids - delivered_fs - newly_built
        in_transit_ids: set[str] = set()
        for c in remaining_transit:
            in_transit_ids.update(c.module_ids)
        launchable = modules_not_delivered - in_transit_ids

        # --- Try launching cargo (respect pad turnaround AND lead time per vehicle) ---
        if launchable and self._delivery_cache:
            eligible_cargo = {
                name: data
                for name, data in self._delivery_cache.items()
                if (period - last_launch.get(name, -999) >= self.config.pad_turnaround_periods
                    and period >= self._cargo_lead.get(name, 0))
            }
            if eligible_cargo:
                best_vehicle_name = max(
                    eligible_cargo, key=lambda k: eligible_cargo[k][0]
                )
                best_mass, transit_p, base_cost = eligible_cargo[best_vehicle_name]

                # Apply first-flight premium if this vehicle has never launched
                is_first_flight = last_launch.get(best_vehicle_name, -999) < 0
                premium = self._cargo_premium.get(best_vehicle_name, 0.0) if is_first_flight else 0.0
                cost = base_cost * (1.0 + premium)

                manifest: list[str] = []
                mass_remaining = best_mass
                for mid in sorted(launchable):
                    mod = self.dag.get_module(mid)
                    if mod.mass_kg <= mass_remaining:
                        manifest.append(mid)
                        mass_remaining -= mod.mass_kg

                if manifest:
                    new_last_launch = dict(last_launch)
                    new_last_launch[best_vehicle_name] = period
                    new_transit = remaining_transit + [
                        CargoInTransit(tuple(manifest), period + transit_p, cost)
                    ]
                    launch_actions = actions + [
                        f"launched:{best_vehicle_name}:{','.join(manifest)}"
                    ]
                    launch_state = SimState(
                        modules_built=new_modules_built,
                        crew_vehicles=active_crew,
                        cargo_in_transit=new_transit,
                        cargo_at_site=state.cargo_at_site,
                        tugs_available=new_tugs,
                        period=period + 1,
                        total_launches=state.total_launches + 1,
                        total_cost_million=state.total_cost_million + cost,
                        cumulative_risk=state.cumulative_risk + risk,
                    )
                    successors.append(
                        (launch_state, delivered_fs, new_wip, new_last_launch, launch_actions)
                    )

        # --- Try sending crew if none on-site (respect pad turnaround AND lead time) ---
        if total_crew == 0 and self.config.crew_vehicles:
            eligible_crew = [
                cv for cv in self.config.crew_vehicles
                if (period - last_launch.get(cv.name, -999) >= self.config.pad_turnaround_periods
                    and period >= self._crew_lead.get(cv.name, 0))
            ]
            if eligible_crew:
                cv = min(eligible_crew, key=lambda v: v.cost_per_launch_million)
                crew_count = min(cv.max_crew, 5)
                rotation_periods = cv.max_mission_duration_days // self.config.period_days
                is_first_flight = last_launch.get(cv.name, -999) < 0
                premium = self._crew_premium.get(cv.name, 0.0) if is_first_flight else 0.0
                crew_cost = cv.cost_per_launch_million * (1.0 + premium)

                new_crew = active_crew + [
                    DockedCrewVehicle(cv.name, crew_count, rotation_periods)
                ]
                new_last_launch_crew = dict(last_launch)
                new_last_launch_crew[cv.name] = period

                crew_actions = actions + [f"crew_launch:{cv.name}:{crew_count}"]
                crew_state_new = SimState(
                    modules_built=new_modules_built,
                    crew_vehicles=new_crew,
                    cargo_in_transit=remaining_transit,
                    cargo_at_site=state.cargo_at_site,
                    tugs_available=new_tugs,
                    period=period + 1,
                    total_launches=state.total_launches + 1,
                    total_cost_million=state.total_cost_million + crew_cost,
                    cumulative_risk=state.cumulative_risk + risk,
                )
                successors.append(
                    (crew_state_new, delivered_fs, new_wip, new_last_launch_crew, crew_actions)
                )

        # --- Combined: launch cargo + crew (both must satisfy lead time) ---
        if (
            total_crew == 0
            and launchable
            and self._delivery_cache
            and self.config.crew_vehicles
        ):
            eligible_cargo_c = {
                name: data
                for name, data in self._delivery_cache.items()
                if (period - last_launch.get(name, -999) >= self.config.pad_turnaround_periods
                    and period >= self._cargo_lead.get(name, 0))
            }
            eligible_crew_c = [
                cv for cv in self.config.crew_vehicles
                if (period - last_launch.get(cv.name, -999) >= self.config.pad_turnaround_periods
                    and period >= self._crew_lead.get(cv.name, 0))
            ]
            if eligible_cargo_c and eligible_crew_c:
                cv = min(eligible_crew_c, key=lambda v: v.cost_per_launch_million)
                crew_count = min(cv.max_crew, 5)
                rotation_periods = cv.max_mission_duration_days // self.config.period_days
                best_vehicle_name = max(
                    eligible_cargo_c, key=lambda k: eligible_cargo_c[k][0]
                )
                best_mass, transit_p, base_cost = eligible_cargo_c[best_vehicle_name]

                cargo_is_first = last_launch.get(best_vehicle_name, -999) < 0
                cargo_premium = self._cargo_premium.get(best_vehicle_name, 0.0) if cargo_is_first else 0.0
                cargo_cost = base_cost * (1.0 + cargo_premium)

                crew_is_first = last_launch.get(cv.name, -999) < 0
                crew_premium = self._crew_premium.get(cv.name, 0.0) if crew_is_first else 0.0
                crew_cost = cv.cost_per_launch_million * (1.0 + crew_premium)

                manifest = []
                mass_remaining = best_mass
                for mid in sorted(launchable):
                    mod = self.dag.get_module(mid)
                    if mod.mass_kg <= mass_remaining:
                        manifest.append(mid)
                        mass_remaining -= mod.mass_kg

                if manifest:
                    new_last_launch_combined = dict(last_launch)
                    new_last_launch_combined[best_vehicle_name] = period
                    new_last_launch_combined[cv.name] = period

                    combined_state = SimState(
                        modules_built=new_modules_built,
                        crew_vehicles=active_crew
                        + [DockedCrewVehicle(cv.name, crew_count, rotation_periods)],
                        cargo_in_transit=remaining_transit
                        + [CargoInTransit(tuple(manifest), period + transit_p, cargo_cost)],
                        cargo_at_site=state.cargo_at_site,
                        tugs_available=new_tugs,
                        period=period + 1,
                        total_launches=state.total_launches + 2,
                        total_cost_million=state.total_cost_million + cargo_cost + crew_cost,
                        cumulative_risk=state.cumulative_risk + risk,
                    )
                    combined_actions = actions + [
                        f"launched:{best_vehicle_name}:{','.join(manifest)}",
                        f"crew_launch:{cv.name}:{crew_count}",
                    ]
                    successors.append(
                        (combined_state, delivered_fs, new_wip, new_last_launch_combined, combined_actions)
                    )

        return successors

    def _make_result(self, state: SimState, timeline: list[dict]) -> SolverResult:
        return SolverResult(
            total_launches=state.total_launches,
            total_periods=state.period,
            total_cost_million=state.total_cost_million,
            modules_completed=len(state.modules_built),
            cumulative_risk=state.cumulative_risk,
            timeline=timeline,
            final_state=state,
        )
