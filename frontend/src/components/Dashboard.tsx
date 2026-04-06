"use client";

import MetricsSummary from "./MetricsSummary";
import GanttChart from "./GanttChart";
import ResourceCharts from "./ResourceCharts";
import CostBreakdown from "./CostBreakdown";
import ParetoPlot from "./ParetoPlot";
import AssemblyView from "./AssemblyView";
import PlaybackControls from "./PlaybackControls";

export default function Dashboard() {
  return (
    <div className="flex-1 h-full overflow-y-auto p-4 bg-gray-950 text-white">
      <h2 className="text-lg font-bold mb-4">Mission Assembly Dashboard</h2>
      <MetricsSummary />
      <PlaybackControls />
      <AssemblyView />
      <div className="grid grid-cols-2 gap-4">
        <GanttChart />
        <ResourceCharts />
        <CostBreakdown />
        <ParetoPlot />
      </div>
    </div>
  );
}
