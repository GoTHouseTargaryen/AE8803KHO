"use client";

import { useSimStore } from "@/store/useSimStore";

export default function MetricsSummary() {
  const result = useSimStore((s) => s.result);
  if (!result) return null;

  const metrics = [
    { label: "Total Launches", value: result.total_launches },
    { label: "Total Time", value: `${result.total_periods} periods (${(result.total_periods * 7 / 30).toFixed(1)} months)` },
    { label: "Total Cost", value: `$${result.total_cost_million.toFixed(0)}M` },
    { label: "Modules Completed", value: result.modules_completed },
    { label: "Cumulative Risk", value: result.cumulative_risk.toFixed(4) },
  ];

  return (
    <div className="grid grid-cols-5 gap-2 mb-4">
      {metrics.map((m) => (
        <div key={m.label} className="bg-gray-800 rounded p-3 text-center">
          <div className="text-xs text-gray-400">{m.label}</div>
          <div className="text-lg font-bold text-white">{m.value}</div>
        </div>
      ))}
    </div>
  );
}
