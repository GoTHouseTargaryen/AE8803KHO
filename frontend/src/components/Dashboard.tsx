"use client";

import MetricsSummary from "./MetricsSummary";
import GanttChart from "./GanttChart";
import ResourceCharts from "./ResourceCharts";
import DecisionLog from "./DecisionLog";
import CostBreakdown from "./CostBreakdown";
import ParetoPlot from "./ParetoPlot";
import AssemblyView from "./AssemblyView";
import PlaybackControls from "./PlaybackControls";
import TaggedRunsSidebar from "./TaggedRunsSidebar";
import CompileReportButton from "./CompileReportButton";

export default function Dashboard() {
  return (
    <div className="flex-1 h-full overflow-y-auto p-4 bg-gray-950 text-white">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">Mission Assembly Dashboard</h2>
        <CompileReportButton />
      </div>
      <TaggedRunsSidebar />
      <MetricsSummary />
      <PlaybackControls />
      <AssemblyView />
      <div className="mb-4">
        <GanttChart />
      </div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <ResourceCharts />
        <DecisionLog />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <CostBreakdown />
        <ParetoPlot />
      </div>
    </div>
  );
}
