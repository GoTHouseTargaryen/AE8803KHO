"use client";

import { useEffect } from "react";
import { useSimStore } from "@/store/useSimStore";
import { getCargoVehicles, getCrewVehicles, getTransferStages, runSimulation } from "@/lib/api";
import VehicleSelector from "./VehicleSelector";
import WeightSliders from "./WeightSliders";
import ModuleEditor from "./ModuleEditor";
import type { SimulationRequest } from "@/lib/types";

export default function ConfigPanel() {
  const store = useSimStore();

  useEffect(() => {
    Promise.all([getCargoVehicles(), getCrewVehicles(), getTransferStages()])
      .then(([cargo, crew, stages]) => store.setCatalogs(cargo, crew, stages))
      .catch(console.error);
  }, []);

  const handleRun = async () => {
    store.setIsRunning(true);
    store.setResult(null);
    try {
      const request: SimulationRequest = {
        spacecraft: store.spacecraft,
        cargo_vehicles: store.selectedCargo,
        crew_vehicles: store.selectedCrew,
        transfer_stages: store.selectedStages,
        weights: store.weights,
        proximity: store.proximity,
        period_days: store.periodDays,
        beam_width: store.beamWidth,
        max_periods: store.maxPeriods,
        max_eva_hours_per_session: store.maxEvaHours,
        max_pairs_per_iva: store.maxPairsPerIva,
        robotic_time_penalty: store.roboticTimePenalty,
      };
      const result = await runSimulation(request);
      store.setResult(result);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      store.setIsRunning(false);
    }
  };

  return (
    <div className="w-80 h-full overflow-y-auto border-r border-gray-700 p-4 bg-gray-900 text-white">
      <h2 className="text-lg font-bold mb-4">Configuration</h2>
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-2">Spacecraft</h3>
        <label className="block text-sm mb-1">Length (km): {store.spacecraft.length_km}</label>
        <input type="range" min="0.5" max="5" step="0.5" value={store.spacecraft.length_km}
          onChange={(e) => store.setSpacecraft({ length_km: parseFloat(e.target.value) })} className="w-full mb-2" />
        <label className="block text-sm mb-1">Propulsion</label>
        <select value={store.spacecraft.propulsion_type}
          onChange={(e) => store.setSpacecraft({ propulsion_type: e.target.value })}
          className="w-full bg-gray-800 rounded p-1 text-sm mb-2">
          <option value="Chemical">Chemical (LOX/LH2)</option>
          <option value="NTP">Nuclear Thermal (NTP)</option>
          <option value="NEP">Nuclear Electric (NEP)</option>
          <option value="SEP">Solar Electric (SEP)</option>
        </select>
        <label className="block text-sm mb-1">Power System</label>
        <select value={store.spacecraft.power_type}
          onChange={(e) => store.setSpacecraft({ power_type: e.target.value })}
          className="w-full bg-gray-800 rounded p-1 text-sm mb-2">
          <option value="Solar">Solar Array</option>
          <option value="Fission">Fission Reactor</option>
          <option value="Fusion">Fusion Reactor</option>
        </select>
      </div>
      <ModuleEditor />
      <VehicleSelector title="Cargo Vehicles" vehicles={store.cargoVehicles} selected={store.selectedCargo} onChange={store.setSelectedCargo} />
      <VehicleSelector title="Crew Vehicles" vehicles={store.crewVehicles} selected={store.selectedCrew} onChange={store.setSelectedCrew} />
      <VehicleSelector title="Transfer Stages"
        vehicles={store.transferStages.map((s) => ({ name: s.name, nation: s.reusable ? "Reusable" : "Expendable" }))}
        selected={store.selectedStages} onChange={store.setSelectedStages} />
      <WeightSliders />
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-2">Crew Parameters</h3>
        <label className="flex justify-between text-sm"><span>EVA hours/session</span><span>{store.maxEvaHours}</span></label>
        <input type="range" min="4" max="8" step="1" value={store.maxEvaHours}
          onChange={(e) => store.setMaxEvaHours(parseInt(e.target.value))} className="w-full mb-2" />
        <label className="flex justify-between text-sm"><span>Max pairs per IVA</span><span>{store.maxPairsPerIva}</span></label>
        <input type="range" min="1" max="4" step="1" value={store.maxPairsPerIva}
          onChange={(e) => store.setMaxPairsPerIva(parseInt(e.target.value))} className="w-full mb-2" />
        <label className="flex justify-between text-sm"><span>Robotic time penalty</span><span>{store.roboticTimePenalty}x</span></label>
        <input type="range" min="1" max="3" step="0.25" value={store.roboticTimePenalty}
          onChange={(e) => store.setRoboticTimePenalty(parseFloat(e.target.value))} className="w-full mb-2" />
      </div>
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-2">Proximity Model</h3>
        <label className="flex justify-between text-sm"><span>Alpha</span><span>{store.proximity.alpha}</span></label>
        <input type="range" min="0.01" max="0.5" step="0.01" value={store.proximity.alpha}
          onChange={(e) => store.setProximity({ alpha: parseFloat(e.target.value) })} className="w-full mb-2" />
        <label className="flex justify-between text-sm"><span>Beta</span><span>{store.proximity.beta}</span></label>
        <input type="range" min="1" max="3" step="0.1" value={store.proximity.beta}
          onChange={(e) => store.setProximity({ beta: parseFloat(e.target.value) })} className="w-full mb-2" />
      </div>
      <button onClick={handleRun} disabled={store.isRunning}
        className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold">
        {store.isRunning ? "Running..." : "Run Simulation"}
      </button>
    </div>
  );
}
