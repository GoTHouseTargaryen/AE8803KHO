import { create } from "zustand";
import type {
  CargoVehicle,
  CrewVehicle,
  TransferStage,
  SpacecraftConfig,
  ObjectiveWeights,
  ProximityConfig,
  SimulationResult,
  TaggedRun,
  SimulationRequest,
} from "@/lib/types";

interface SimStore {
  cargoVehicles: CargoVehicle[];
  crewVehicles: CrewVehicle[];
  transferStages: TransferStage[];
  selectedCargo: string[];
  selectedCrew: string[];
  selectedStages: string[];
  spacecraft: SpacecraftConfig;
  weights: ObjectiveWeights;
  proximity: ProximityConfig;
  periodDays: number;
  beamWidth: number;
  maxPeriods: number;
  maxEvaHours: number;
  maxPairsPerIva: number;
  roboticTimePenalty: number;
  isRunning: boolean;
  result: SimulationResult | null;
  currentPeriod: number;
  isPlaying: boolean;
  playbackSpeed: number;
  // Report tagging
  taggedRuns: TaggedRun[];
  reportStatus: "idle" | "compiling" | "done" | "error";
  reportUrl: string | null;
  reportError: string | null;
  setCatalogs: (cargo: CargoVehicle[], crew: CrewVehicle[], stages: TransferStage[]) => void;
  setSelectedCargo: (names: string[]) => void;
  setSelectedCrew: (names: string[]) => void;
  setSelectedStages: (names: string[]) => void;
  setSpacecraft: (config: Partial<SpacecraftConfig>) => void;
  setWeights: (weights: Partial<ObjectiveWeights>) => void;
  setProximity: (config: Partial<ProximityConfig>) => void;
  setPeriodDays: (days: number) => void;
  setBeamWidth: (width: number) => void;
  setMaxPeriods: (periods: number) => void;
  setMaxEvaHours: (hours: number) => void;
  setMaxPairsPerIva: (pairs: number) => void;
  setRoboticTimePenalty: (penalty: number) => void;
  setIsRunning: (running: boolean) => void;
  setResult: (result: SimulationResult | null) => void;
  setCurrentPeriod: (period: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
  // Report actions
  addTaggedRun: (run: TaggedRun) => void;
  removeTaggedRun: (id: string) => void;
  updateTaggedRunLabel: (id: string, label: string) => void;
  setReportStatus: (status: "idle" | "compiling" | "done" | "error") => void;
  setReportUrl: (url: string | null) => void;
  setReportError: (error: string | null) => void;
}

export const useSimStore = create<SimStore>((set) => ({
  cargoVehicles: [],
  crewVehicles: [],
  transferStages: [],
  selectedCargo: ["Starship"],
  selectedCrew: ["Crew Dragon"],
  selectedStages: ["Chemical Kick Stage"],
  spacecraft: { length_km: 1.0, structure_type: "truss", propulsion_type: "Chemical", power_type: "Solar" },
  weights: { w_launches: 1.0, w_time: 1.0, w_cost: 1.0 },
  proximity: { alpha: 0.1, beta: 1.5, base_capacity: 2, max_capacity: 10 },
  periodDays: 7,
  beamWidth: 100,
  maxPeriods: 200,
  maxEvaHours: 6,
  maxPairsPerIva: 2,
  roboticTimePenalty: 1.5,
  isRunning: false,
  result: null,
  currentPeriod: 0,
  isPlaying: false,
  playbackSpeed: 1,
  taggedRuns: [],
  reportStatus: "idle",
  reportUrl: null,
  reportError: null,
  setCatalogs: (cargo, crew, stages) => set({ cargoVehicles: cargo, crewVehicles: crew, transferStages: stages }),
  setSelectedCargo: (names) => set({ selectedCargo: names }),
  setSelectedCrew: (names) => set({ selectedCrew: names }),
  setSelectedStages: (names) => set({ selectedStages: names }),
  setSpacecraft: (config) => set((s) => ({ spacecraft: { ...s.spacecraft, ...config } })),
  setWeights: (weights) => set((s) => ({ weights: { ...s.weights, ...weights } })),
  setProximity: (config) => set((s) => ({ proximity: { ...s.proximity, ...config } })),
  setPeriodDays: (days) => set({ periodDays: days }),
  setBeamWidth: (width) => set({ beamWidth: width }),
  setMaxPeriods: (periods) => set({ maxPeriods: periods }),
  setMaxEvaHours: (hours) => set({ maxEvaHours: hours }),
  setMaxPairsPerIva: (pairs) => set({ maxPairsPerIva: pairs }),
  setRoboticTimePenalty: (penalty) => set({ roboticTimePenalty: penalty }),
  setIsRunning: (running) => set({ isRunning: running }),
  setResult: (result) => set({ result, currentPeriod: 0, isPlaying: false }),
  setCurrentPeriod: (period) => set({ currentPeriod: period }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),
  addTaggedRun: (run) => set((s) => ({ taggedRuns: [...s.taggedRuns, run] })),
  removeTaggedRun: (id) => set((s) => ({ taggedRuns: s.taggedRuns.filter((r) => r.id !== id) })),
  updateTaggedRunLabel: (id, label) =>
    set((s) => ({
      taggedRuns: s.taggedRuns.map((r) => (r.id === id ? { ...r, label } : r)),
    })),
  setReportStatus: (status) => set({ reportStatus: status }),
  setReportUrl: (url) => set({ reportUrl: url }),
  setReportError: (error) => set({ reportError: error }),
}));
