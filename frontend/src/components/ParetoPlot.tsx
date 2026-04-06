"use client";

import { useSimStore } from "@/store/useSimStore";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ZAxis } from "recharts";

export default function ParetoPlot() {
  const result = useSimStore((s) => s.result);
  if (!result) return null;

  const data = [{ launches: result.total_launches, time: result.total_periods, cost: result.total_cost_million }];

  return (
    <div className="bg-gray-800 rounded p-3 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">Solution Space (Launches vs Time)</h3>
      <ResponsiveContainer width="100%" height={200}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="launches" name="Launches" tick={{ fill: "#aaa", fontSize: 11 }}
            label={{ value: "Launches", position: "bottom", fill: "#aaa", fontSize: 11 }} />
          <YAxis dataKey="time" name="Periods" tick={{ fill: "#aaa", fontSize: 11 }}
            label={{ value: "Periods", angle: -90, position: "left", fill: "#aaa", fontSize: 11 }} />
          <ZAxis dataKey="cost" range={[100, 400]} name="Cost ($M)" />
          <Tooltip contentStyle={{ backgroundColor: "#333", border: "none" }} labelStyle={{ color: "#fff" }} />
          <Scatter data={data} fill="#22c55e" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
