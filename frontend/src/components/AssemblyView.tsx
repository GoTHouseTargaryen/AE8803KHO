"use client";

import { useRef, useEffect, useMemo } from "react";
import { useSimStore } from "@/store/useSimStore";

const CATEGORY_COLORS: Record<string, string> = {
  structural: "#9ca3af", habitation: "#3b82f6", power: "#eab308",
  thermal: "#06b6d4", propulsion: "#ef4444", avionics: "#a855f7", specialty: "#f97316",
};

const MODULE_HEIGHT = 30;
const MODULE_WIDTH = 60;
const PADDING = 10;

export default function AssemblyView() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const builtModules = useMemo(() => {
    if (!result) return new Set<string>();
    const built = new Set<string>();
    for (const entry of result.timeline) {
      if (entry.period > currentPeriod) break;
      for (const action of entry.actions) {
        if (action.startsWith("assembled:")) built.add(action.split(":")[1]);
      }
    }
    return built;
  }, [result, currentPeriod]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.parentElement?.clientWidth || 800;
    const height = 300;
    canvas.width = width;
    canvas.height = height;

    ctx.fillStyle = "#111827";
    ctx.fillRect(0, 0, width, height);

    const allModuleIds = Array.from(builtModules).sort();
    const trussModules = allModuleIds.filter((id) => id.startsWith("truss_section"));
    const otherModules = allModuleIds.filter((id) => !id.startsWith("truss_section"));

    const trussY = height / 2;
    const startX = PADDING;
    trussModules.forEach((id, i) => {
      const x = startX + i * (MODULE_WIDTH + 4);
      ctx.fillStyle = CATEGORY_COLORS.structural;
      ctx.fillRect(x, trussY - MODULE_HEIGHT / 4, MODULE_WIDTH, MODULE_HEIGHT / 2);
      ctx.strokeStyle = "#555";
      ctx.strokeRect(x, trussY - MODULE_HEIGHT / 4, MODULE_WIDTH, MODULE_HEIGHT / 2);
    });

    let aboveY = trussY - MODULE_HEIGHT - 10;
    let belowY = trussY + MODULE_HEIGHT / 2 + 10;
    let xOffset = startX;
    let above = true;
    otherModules.forEach((id) => {
      let category = "specialty";
      for (const [cat] of Object.entries(CATEGORY_COLORS)) {
        if (id.includes(cat.substring(0, 4))) { category = cat; break; }
      }
      const y = above ? aboveY : belowY;
      above = !above;

      ctx.fillStyle = CATEGORY_COLORS[category] || "#6b7280";
      ctx.fillRect(xOffset, y, MODULE_WIDTH - 10, MODULE_HEIGHT);
      ctx.strokeStyle = "#555";
      ctx.strokeRect(xOffset, y, MODULE_WIDTH - 10, MODULE_HEIGHT);

      ctx.fillStyle = "#fff";
      ctx.font = "9px monospace";
      ctx.fillText(id.substring(0, 10), xOffset + 2, y + MODULE_HEIGHT / 2 + 3);

      xOffset += MODULE_WIDTH - 6;
      if (xOffset > width - MODULE_WIDTH) {
        xOffset = startX;
        aboveY -= MODULE_HEIGHT + 4;
        belowY += MODULE_HEIGHT + 4;
      }
    });

    ctx.fillStyle = "#fff";
    ctx.font = "13px monospace";
    ctx.fillText(`Period: ${currentPeriod}`, width - 150, 20);
    ctx.fillText(`Modules: ${builtModules.size}`, width - 150, 38);
  }, [builtModules, currentPeriod]);

  if (!result) {
    return (
      <div className="bg-gray-800 rounded p-3 mb-4 h-[300px] flex items-center justify-center text-gray-500">
        Run a simulation to see assembly progression
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded p-3 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-300">2D Assembly View</h3>
      <canvas ref={canvasRef} className="w-full" />
    </div>
  );
}
