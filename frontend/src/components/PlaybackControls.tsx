"use client";

import { useEffect, useRef } from "react";
import { useSimStore } from "@/store/useSimStore";

export default function PlaybackControls() {
  const result = useSimStore((s) => s.result);
  const currentPeriod = useSimStore((s) => s.currentPeriod);
  const isPlaying = useSimStore((s) => s.isPlaying);
  const playbackSpeed = useSimStore((s) => s.playbackSpeed);
  const setCurrentPeriod = useSimStore((s) => s.setCurrentPeriod);
  const setIsPlaying = useSimStore((s) => s.setIsPlaying);
  const setPlaybackSpeed = useSimStore((s) => s.setPlaybackSpeed);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isPlaying && result) {
      intervalRef.current = setInterval(() => {
        setCurrentPeriod(
          useSimStore.getState().currentPeriod >= result.total_periods
            ? 0 : useSimStore.getState().currentPeriod + 1
        );
      }, 1000 / playbackSpeed);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [isPlaying, playbackSpeed, result, setCurrentPeriod]);

  if (!result) return null;

  return (
    <div className="bg-gray-800 rounded p-3 mb-4 flex items-center gap-4">
      <button onClick={() => setCurrentPeriod(Math.max(0, currentPeriod - 1))}
        className="px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm">&lt;</button>
      <button onClick={() => setIsPlaying(!isPlaying)}
        className="px-4 py-1 bg-blue-600 rounded hover:bg-blue-700 text-sm font-semibold">
        {isPlaying ? "Pause" : "Play"}
      </button>
      <button onClick={() => { setIsPlaying(false); setCurrentPeriod(0); }}
        className="px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm">Stop</button>
      <button onClick={() => setCurrentPeriod(Math.min(result.total_periods, currentPeriod + 1))}
        className="px-2 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm">&gt;</button>
      <select value={playbackSpeed} onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
        className="bg-gray-700 rounded p-1 text-sm">
        <option value={1}>1x</option><option value={2}>2x</option>
        <option value={5}>5x</option><option value={10}>10x</option>
      </select>
      <input type="range" min="0" max={result.total_periods} value={currentPeriod}
        onChange={(e) => { setIsPlaying(false); setCurrentPeriod(parseInt(e.target.value)); }} className="flex-1" />
      <span className="text-sm text-gray-400 w-24 text-right">{currentPeriod} / {result.total_periods}</span>
    </div>
  );
}
