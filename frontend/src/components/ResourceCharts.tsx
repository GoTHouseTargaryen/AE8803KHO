"use client";

import { useMemo } from "react";
import { useSimStore } from "@/store/useSimStore";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from "recharts";

export default function ResourceCharts() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);

  const data = useMemo(() => {
    if (!result) return [];
    let modulesBuilt = 0;
    let crewOnSite = 0;
    return result.timeline.map((entry) => {
      for (const action of entry.actions) {
        if (action.startsWith("assembled:")) modulesBuilt++;
        if (action.startsWith("crew_launch:")) {
          const parts = action.split(":");
          crewOnSite += parseInt(parts[2]) || 0;
        }
      }
      return { period: entry.period, modules: modulesBuilt, crew: crewOnSite };
    });
  }, [result]);

  if (!result || data.length === 0) return null;

  return (
    <div className="bg-gray-800 rounded p-3 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">Resource Utilization Over Time</h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="period" tick={{ fill: "#aaa", fontSize: 11 }} />
          <YAxis tick={{ fill: "#aaa", fontSize: 11 }} />
          <Tooltip contentStyle={{ backgroundColor: "#333", border: "none" }} labelStyle={{ color: "#fff" }} />
          <Area type="monotone" dataKey="modules" stroke="#22c55e" fill="#22c55e" fillOpacity={0.3} name="Modules Built" />
          <Area type="monotone" dataKey="crew" stroke="#eab308" fill="#eab308" fillOpacity={0.3} name="Crew On-Site" />
          <ReferenceLine x={currentPeriod} stroke="#ef4444" strokeDasharray="3 3" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
