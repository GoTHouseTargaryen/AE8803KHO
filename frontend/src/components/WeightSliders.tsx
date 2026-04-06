"use client";

import { useSimStore } from "@/store/useSimStore";

export default function WeightSliders() {
  const weights = useSimStore((s) => s.weights);
  const setWeights = useSimStore((s) => s.setWeights);

  const sliders = [
    { key: "w_launches" as const, label: "Launches" },
    { key: "w_time" as const, label: "Time" },
    { key: "w_cost" as const, label: "Cost" },
  ];

  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold mb-2">Objective Weights</h3>
      {sliders.map(({ key, label }) => (
        <div key={key} className="mb-2">
          <label className="flex justify-between text-sm">
            <span>{label}</span>
            <span>{weights[key].toFixed(1)}</span>
          </label>
          <input type="range" min="0" max="2" step="0.1" value={weights[key]}
            onChange={(e) => setWeights({ [key]: parseFloat(e.target.value) })} className="w-full" />
        </div>
      ))}
    </div>
  );
}
