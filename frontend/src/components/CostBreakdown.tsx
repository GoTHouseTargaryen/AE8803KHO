"use client";

import { useSimStore } from "@/store/useSimStore";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function CostBreakdown() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);
  if (!result) return null;

  const launchCounts: Record<string, number> = {};
  for (const entry of result.timeline) {
    if (entry.period > currentPeriod) break;
    for (const action of entry.actions) {
      if (action.startsWith("launched:") || action.startsWith("crew_launch:")) {
        const vehicleName = action.split(":")[1];
        launchCounts[vehicleName] = (launchCounts[vehicleName] || 0) + 1;
      }
    }
  }

  const data = Object.entries(launchCounts).map(([name, count]) => ({ name, launches: count }));
  if (data.length === 0) return null;

  return (
    <div className="bg-gray-800 rounded p-3 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">Launches by Vehicle</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="name" tick={{ fill: "#aaa", fontSize: 11 }} />
          <YAxis tick={{ fill: "#aaa", fontSize: 11 }} />
          <Tooltip contentStyle={{ backgroundColor: "#333", border: "none" }} labelStyle={{ color: "#fff" }} />
          <Bar dataKey="launches" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
