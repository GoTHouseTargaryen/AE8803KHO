"use client";

import React, { useMemo } from "react";
import { useSimStore } from "@/store/useSimStore";
import type { TimelineMath } from "@/lib/types";

type ActionBadge = { label: string; color: string };

function parseAction(action: string): ActionBadge {
  if (action.startsWith("assembled:")) {
    return { label: `built: ${action.slice(10)}`, color: "text-green-400 bg-green-900/40" };
  }
  if (action.startsWith("wip:")) {
    const parts = action.split(":");
    return { label: `wip: ${parts[1]} (${parts[2] ?? ""})`, color: "text-yellow-400 bg-yellow-900/40" };
  }
  if (action.startsWith("launched:")) {
    const parts = action.split(":");
    const payload = parts.slice(2).join(":");
    return { label: `launch: ${parts[1]}${payload ? ` [${payload}]` : ""}`, color: "text-blue-400 bg-blue-900/40" };
  }
  if (action.startsWith("crew_launch:")) {
    const parts = action.split(":");
    return { label: `crew: ${parts[1]} x${parts[2] ?? ""}`, color: "text-purple-400 bg-purple-900/40" };
  }
  return { label: action, color: "text-gray-400 bg-gray-700/40" };
}

function Val({ label, value, title, color = "text-gray-300" }: {
  label: string; value: string; title?: string; color?: string;
}) {
  return (
    <span title={title} className="whitespace-nowrap">
      <span className="text-gray-500">{label}=</span>
      <span className={color}>{value}</span>
    </span>
  );
}

function LogSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-900/60 rounded px-2 py-1 space-y-0.5">
      <div className="text-[9px] uppercase tracking-wider text-gray-600 font-semibold">{title}</div>
      {children}
    </div>
  );
}

function DecisionDetail({ m }: { m: TimelineMath }) {
  const f = (v: number, d = 2) => v.toFixed(d);
  const fE = (v: number) => v < 1e-4 ? v.toExponential(2) : f(v, 5);
  const wipEntries = Object.entries(m.wip_modules);

  return (
    <div className="mt-1 font-mono text-[10px] space-y-1 leading-snug">

      <LogSection title="Inputs">
        <div className="flex flex-wrap gap-x-4 gap-y-0.5">
          <Val label="crew_on_site" value={String(m.total_crew)} title="Crew currently docked" />
          <Val
            label="h_crew" value={`${f(m.crew_hours)}h`}
            title={`Raw ${f(m.crew_hours_raw)}h ÷ κ=${f(m.proximity_penalty, 3)} · ${f(m.crew_hours_unused)}h unused`}
          />
          <Val
            label="h_rob" value={`${f(m.robotic_hours)}h`}
            title={`Raw ${f(m.robotic_hours_raw)}h ÷ κ · ${f(m.robotic_hours_unused)}h unused`}
          />
          <Val
            label="κ" value={f(m.proximity_penalty, 3)}
            title={`Proximity congestion penalty — divides available hours. n_prox=${m.n_proximity}`}
          />
          <Val label="n_prox" value={String(m.n_proximity)} title="Vehicles in proximity zone" />
          <Val label="ΔR" value={fE(m.collision_risk_increment)} title="Collision risk increment this period" />
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-gray-400">
          <Val label="dag_unlocked" value={String(m.dag_available_count)} title="Modules whose DAG prerequisites are satisfied" />
          <Val label="buildable" value={String(m.buildable_count)} title="Unlocked AND physically at site" />
          {m.buildable_modules.length > 0 && (
            <span className="text-gray-500 truncate max-w-xs" title={m.buildable_modules.join(", ")}>
              [{m.buildable_modules.slice(0, 4).join(", ")}{m.buildable_modules.length > 4 ? `… +${m.buildable_modules.length - 4}` : ""}]
            </span>
          )}
        </div>
        {(m.eligible_cargo_vehicles.length > 0 || m.eligible_crew_vehicles.length > 0) && (
          <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-gray-400">
            {m.eligible_cargo_vehicles.length > 0 && (
              <span title="Cargo vehicles past pad turnaround and lead-time gates">
                <span className="text-gray-500">eligible_cargo=</span>[{m.eligible_cargo_vehicles.join(", ")}]
              </span>
            )}
            {m.eligible_crew_vehicles.length > 0 && (
              <span title="Crew vehicles eligible for launch (no crew currently on-site)">
                <span className="text-gray-500">eligible_crew=</span>[{m.eligible_crew_vehicles.join(", ")}]
              </span>
            )}
          </div>
        )}
        {wipEntries.length > 0 && (
          <div className="text-yellow-600">
            <span className="text-gray-500">wip=</span>
            {"{"}
            {wipEntries.map(([mid, hrs], i) => (
              <span key={mid}>{i > 0 ? ", " : ""}{mid}: {f(hrs)}h</span>
            ))}
            {"}"}
          </div>
        )}
      </LogSection>

      <LogSection title="Objective  J = w_L·(L/L_max) + w_T·(t/T_max) + w_C·($/C_max)">
        <div className="flex flex-wrap gap-x-4 gap-y-0.5">
          <span>
            <span className="text-gray-500">J=</span>
            <span className="text-white font-bold">{f(m.weighted_cost, 4)}</span>
          </span>
          <Val label="J_L" value={f(m.J_launches, 4)} color="text-blue-400"
            title={`w_launches · (${m.total_launches} / ${m.modules_total * 2})`} />
          <Val label="J_T" value={f(m.J_time, 4)} color="text-yellow-400"
            title="w_time · (period / max_periods)" />
          <Val label="J_C" value={f(m.J_cost, 4)} color="text-green-400"
            title={`w_cost · ($${f(m.total_cost_million)}M / C_max)`} />
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-gray-400">
          <Val
            label="built" value={`${m.modules_built}/${m.modules_total}`}
            title={`${m.progress_pct.toFixed(1)}% complete`}
          />
          <Val
            label="L" value={`${m.total_launches}${m.launches_this_period > 0 ? ` (+${m.launches_this_period})` : ""}`}
            title="Cumulative launches (delta this period)"
          />
          <Val
            label="$" value={`${f(m.total_cost_million)}M${m.cost_this_period > 0 ? ` (+${f(m.cost_this_period)}M)` : ""}`}
            title="Cumulative program cost (delta this period)"
          />
        </div>
      </LogSection>

      {(m.pending_deliveries.length > 0 || m.crew_rotations.length > 0) && (
        <LogSection title="Next Step  (pipeline entering next iteration)">
          {m.pending_deliveries.length > 0 && (
            <div className="text-gray-400">
              <span className="text-gray-500">transit=</span>
              {m.pending_deliveries.map((d, i) => (
                <span key={i}>{i > 0 ? " · " : ""}
                  [{d.modules.length} mod] →P{d.arrival_period} (+{d.periods_until}p)
                </span>
              ))}
            </div>
          )}
          {m.crew_rotations.length > 0 && (
            <div className="text-gray-400">
              <span className="text-gray-500">crew=</span>
              {m.crew_rotations.map((c, i) => (
                <span key={i}>{i > 0 ? " · " : ""}
                  {c.vehicle}×{c.crew} ({c.periods_remaining}p left)
                </span>
              ))}
            </div>
          )}
        </LogSection>
      )}
    </div>
  );
}

export default function DecisionLog() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);

  const entries = useMemo(() => {
    if (!result) return [];
    return result.timeline;
  }, [result]);

  if (!result || entries.length === 0) return null;

  return (
    <div className="bg-gray-800 rounded p-3">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">Optimizer Decision Log</h3>
      <div className="overflow-y-auto h-[200px] space-y-0.5 pr-1">
        {entries.map((entry) => {
          const isActive = entry.period === currentPeriod;
          return (
            <div
              key={entry.period}
              className={`px-2 py-1 rounded text-xs ${
                isActive ? "bg-red-900/30 ring-1 ring-red-700/60" : "hover:bg-gray-700/40"
              }`}
            >
              <div className="flex flex-wrap items-start gap-1">
                <span className={`font-mono font-bold shrink-0 w-8 ${isActive ? "text-red-400" : "text-gray-500"}`}>
                  P{entry.period}
                </span>
                {entry.actions.length > 0
                  ? entry.actions.map((action, i) => {
                      const { label, color } = parseAction(action);
                      return (
                        <span key={i} className={`px-1 rounded ${color}`}>{label}</span>
                      );
                    })
                  : <span className="text-gray-600 italic">idle — beam advance only</span>
                }
              </div>
              {entry.math && <DecisionDetail m={entry.math} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
