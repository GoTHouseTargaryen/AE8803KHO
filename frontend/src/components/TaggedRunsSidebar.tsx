"use client";

import { useState } from "react";
import { useSimStore } from "@/store/useSimStore";

export default function TaggedRunsSidebar() {
  const taggedRuns = useSimStore((s) => s.taggedRuns);
  const removeTaggedRun = useSimStore((s) => s.removeTaggedRun);
  const updateTaggedRunLabel = useSimStore((s) => s.updateTaggedRunLabel);
  const [collapsed, setCollapsed] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  if (taggedRuns.length === 0) return null;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded p-3 mb-4">
      <div
        className="flex justify-between items-center cursor-pointer"
        onClick={() => setCollapsed((c) => !c)}
      >
        <span className="text-sm font-semibold text-white">
          Tagged for Report ({taggedRuns.length})
        </span>
        <span className="text-gray-400 text-xs">{collapsed ? "show" : "hide"}</span>
      </div>

      {!collapsed && (
        <ul className="mt-2 space-y-1">
          {taggedRuns.map((run) => (
            <li key={run.id} className="flex items-center gap-2">
              {editingId === run.id ? (
                <>
                  <input
                    className="bg-gray-700 text-white text-xs px-2 py-0.5 rounded flex-1 border border-gray-500"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        updateTaggedRunLabel(run.id, editValue);
                        setEditingId(null);
                      }
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    autoFocus
                  />
                  <button
                    className="text-green-400 text-xs hover:text-green-300"
                    onClick={() => {
                      updateTaggedRunLabel(run.id, editValue);
                      setEditingId(null);
                    }}
                  >
                    done
                  </button>
                </>
              ) : (
                <>
                  <span
                    className="text-xs text-gray-300 flex-1 truncate cursor-pointer hover:text-white"
                    title="Click to rename"
                    onClick={() => {
                      setEditingId(run.id);
                      setEditValue(run.label);
                    }}
                  >
                    {run.label}
                  </span>
                  <span className="text-xs text-gray-500">
                    {run.result.total_launches}L / {run.result.total_periods}p
                  </span>
                  <button
                    className="text-gray-500 hover:text-red-400 text-xs leading-none"
                    onClick={() => removeTaggedRun(run.id)}
                    title="Remove from report"
                  >
                    x
                  </button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
