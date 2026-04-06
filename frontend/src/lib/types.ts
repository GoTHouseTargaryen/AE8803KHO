export interface CargoVehicle {
  name: string;
  nation: string;
  payload_to_leo_kg: number;
  fairing_volume_m3: number;
  cost_per_launch_million: number;
  l4_direct: boolean;
  status: string;
}

export interface CrewVehicle {
  name: string;
  nation: string;
  max_crew: number;
  max_mission_duration_days: number;
  mass_kg: number;
  l4_direct: boolean;
  mass_per_crew_kg: number;
}

export interface TransferStage {
  name: string;
  dry_mass_kg: number;
  propellant_kg: number;
  isp_s: number;
  reusable: boolean;
}

export interface ModuleDef {
  type: string;
  mass_kg: number;
  assembly_hours: number;
  crew_required: boolean;
  category: string;
  power_output_kw?: number;
  isp?: number;
  thrust_level?: string;
  required_power_system?: string;
}

export interface GeneratedModule extends ModuleDef {
  id: string;
}

export interface SpacecraftConfig {
  length_km: number;
  structure_type: string;
  propulsion_type: string;
  power_type: string;
}

export interface GenerateResult {
  modules: GeneratedModule[];
  dependencies: Record<string, string[]>;
}

export interface ObjectiveWeights {
  w_launches: number;
  w_time: number;
  w_cost: number;
}

export interface ProximityConfig {
  alpha: number;
  beta: number;
  base_capacity: number;
  max_capacity: number;
}

export interface SimulationRequest {
  spacecraft: SpacecraftConfig;
  cargo_vehicles: string[];
  crew_vehicles: string[];
  transfer_stages: string[];
  weights: ObjectiveWeights;
  proximity: ProximityConfig;
  period_days: number;
  beam_width: number;
  max_periods: number;
  max_eva_hours_per_session: number;
  max_pairs_per_iva: number;
  robotic_time_penalty: number;
}

export interface TimelineEntry {
  period: number;
  actions: string[];
}

export interface SimulationResult {
  total_launches: number;
  total_periods: number;
  total_cost_million: number;
  modules_completed: number;
  cumulative_risk: number;
  timeline: TimelineEntry[];
}
