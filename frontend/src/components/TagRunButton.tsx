"use client";

import { useState } from "react";
import { useSimStore } from "@/store/useSimStore";
import type { TaggedRun } from "@/lib/types";

export default function TagRunButton() {
  const result = useSimStore((s) => s.result);
  const spacecraft = useSimStore((s) => s.spacecraft);
  const weights = useSimStore((s) => s.weights);
  const proximity = useSimStore((s) => s.proximity);
  const selectedCargo = useSimStore((s) => s.selectedCargo);
  const selectedCrew = useSimStore((s) => s.selectedCrew);
  const selectedStages = useSimStore((s) => s.selectedStages);
  const periodDays = useSimStore((s) => s.periodDays);
  const beamWidth = useSimStore((s) => s.beamWidth);
  const maxPeriods = useSimStore((s) => s.maxPeriods);
  const taggedRuns = useSimStore((s) => s.taggedRuns);
  const addTaggedRun = useSimStore((s) => s.addTaggedRun);
  const removeTaggedRun = useSimStore((s) => s.removeTaggedRun);

  const [labeling, setLabeling] = useState(false);
  const [label, setLabel] = useState("");

  if (!result) return null;

  const currentKey = `${result.total_launches}-${result.total_periods}-${result.total_cost_million}`;
  const existingTag = taggedRuns.find(
    (r) =>
      `${r.result.total_launches}-${r.result.total_periods}-${r.result.total_cost_million}` ===
      currentKey
  );

  if (existingTag) {
    return (
      <button
        className="mt-2 px-3 py-1 bg-green-700 text-white text-xs rounded hover:bg-red-700 transition-colors"
        onClick={() => removeTaggedRun(existingTag.id)}
        title="Click to remove from report"
      >
        Tagged for Report (click to remove)
      </button>
    );
  }

  if (labeling) {
    return (
      <div className="mt-2 flex gap-2 items-center">
        <input
          className="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-500 flex-1"
          placeholder="Run label (e.g. Baseline — Chemical/Solar 0.5km)"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") confirmTag();
            if (e.key === "Escape") setLabeling(false);
          }}
          autoFocus
        />
        <button
          className="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
          onClick={confirmTag}
        >
          Add
        </button>
        <button
          className="px-2 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-500"
          onClick={() => setLabeling(false)}
        >
          Cancel
        </button>
      </div>
    );
  }

  function confirmTag() {
    if (!result) return;
    const run: TaggedRun = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      label: label.trim() || `Run ${taggedRuns.length + 1}`,
      config: {
        spacecraft,
        cargo_vehicles: selectedCargo,
        crew_vehicles: selectedCrew,
        transfer_stages: selectedStages,
        weights,
        proximity,
        period_days: periodDays,
        beam_width: beamWidth,
        max_periods: maxPeriods,
        max_eva_hours_per_session: 6,
        max_pairs_per_iva: 2,
        robotic_time_penalty: 1.5,
      },
      result,
      taggedAt: new Date().toISOString(),
    };
    addTaggedRun(run);
    setLabeling(false);
    setLabel("");
  }

  return (
    <button
      className="mt-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
      onClick={() => setLabeling(true)}
    >
      + Tag for Report
    </button>
  );
}
