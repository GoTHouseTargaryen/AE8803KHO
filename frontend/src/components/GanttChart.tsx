"use client";

import { useMemo, useRef, useEffect } from "react";
import { useSimStore } from "@/store/useSimStore";

const COLORS: Record<string, string> = { assembled: "#22c55e", launched: "#3b82f6", crew_launch: "#eab308" };
const ROW_HEIGHT = 20;
const PERIOD_WIDTH = 12;
const LEFT_MARGIN = 120;

export default function GanttChart() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const events = useMemo(() => {
    if (!result) return [];
    const evts: { label: string; period: number; type: string }[] = [];
    for (const entry of result.timeline) {
      for (const action of entry.actions) {
        const [type, ...rest] = action.split(":");
        const label = rest.join(":").substring(0, 20);
        evts.push({ label, period: entry.period, type });
      }
    }
    return evts;
  }, [result]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !result) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const totalPeriods = result.total_periods;
    const width = LEFT_MARGIN + totalPeriods * PERIOD_WIDTH + 20;
    const height = events.length * ROW_HEIGHT + 40;
    canvas.width = width;
    canvas.height = height;

    ctx.fillStyle = "#1f2937";
    ctx.fillRect(0, 0, width, height);

    events.forEach((evt, i) => {
      const y = i * ROW_HEIGHT + 20;
      const x = LEFT_MARGIN + evt.period * PERIOD_WIDTH;
      ctx.fillStyle = "#9ca3af";
      ctx.font = "11px monospace";
      ctx.fillText(evt.label, 4, y + 14);
      ctx.fillStyle = COLORS[evt.type] || "#6b7280";
      ctx.fillRect(x, y + 2, PERIOD_WIDTH - 2, ROW_HEIGHT - 4);
    });

    const cpX = LEFT_MARGIN + currentPeriod * PERIOD_WIDTH;
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(cpX, 0);
    ctx.lineTo(cpX, height);
    ctx.stroke();
  }, [events, currentPeriod, result]);

  if (!result) return null;

  return (
    <div className="bg-gray-800 rounded p-3 mb-4 overflow-x-auto">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">Assembly Timeline</h3>
      <canvas ref={canvasRef} className="max-w-full" />
    </div>
  );
}
