import type {
  CargoVehicle,
  CrewVehicle,
  TransferStage,
  ModuleDef,
  GenerateResult,
  SimulationRequest,
  SimulationResult,
  ParetoRequest,
  ParetoResult,
  TaggedRun,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`);
  }
  return resp.json() as Promise<T>;
}

export async function getCargoVehicles(): Promise<CargoVehicle[]> {
  return fetchJson("/api/catalog/cargo-vehicles");
}

export async function getCrewVehicles(): Promise<CrewVehicle[]> {
  return fetchJson("/api/catalog/crew-vehicles");
}

export async function getTransferStages(): Promise<TransferStage[]> {
  return fetchJson("/api/catalog/transfer-stages");
}

export async function getModuleCatalog(): Promise<ModuleDef[]> {
  return fetchJson("/api/catalog/modules");
}

export async function generateSpacecraft(
  config: { length_km: number; structure_type: string; propulsion_type: string; power_type: string }
): Promise<GenerateResult> {
  return fetchJson("/api/generate", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function runSimulation(
  request: SimulationRequest
): Promise<SimulationResult> {
  return fetchJson("/api/simulate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function runPareto(request: ParetoRequest): Promise<ParetoResult> {
  return fetchJson("/api/pareto", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function compileReport(runs: TaggedRun[]): Promise<Blob> {
  const resp = await fetch(`${API_BASE}/api/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ runs }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Report compilation failed: ${text}`);
  }
  return resp.blob();
}
