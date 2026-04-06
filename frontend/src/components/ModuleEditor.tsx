"use client";

import { useState } from "react";
import { generateSpacecraft } from "@/lib/api";
import { useSimStore } from "@/store/useSimStore";
import type { GeneratedModule } from "@/lib/types";

export default function ModuleEditor() {
  const spacecraft = useSimStore((s) => s.spacecraft);
  const [modules, setModules] = useState<GeneratedModule[]>([]);
  const [loading, setLoading] = useState(false);

  const loadModules = async () => {
    setLoading(true);
    try {
      const result = await generateSpacecraft(spacecraft);
      setModules(result.modules);
    } catch (err) {
      console.error("Failed to generate spacecraft:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">Module Preview</h3>
        <button onClick={loadModules} disabled={loading}
          className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded">
          {loading ? "..." : "Preview"}
        </button>
      </div>
      {modules.length > 0 && (
        <div className="max-h-40 overflow-y-auto text-xs space-y-1">
          {modules.map((m) => (
            <div key={m.id} className="flex justify-between bg-gray-800 rounded px-2 py-1">
              <span>{m.type}</span>
              <span className="text-gray-400">{m.mass_kg.toLocaleString()} kg</span>
            </div>
          ))}
          <div className="text-gray-400 mt-1">
            Total: {modules.length} modules, {modules.reduce((s, m) => s + m.mass_kg, 0).toLocaleString()} kg
          </div>
        </div>
      )}
    </div>
  );
}
