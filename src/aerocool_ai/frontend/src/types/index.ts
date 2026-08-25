export interface HotspotProperties {
  hotspot_id: string;
  lst_celsius: number;
  uhi_intensity_celsius: number;
  regional_mean_lst: number;
  heat_vulnerability_index: number;
  dominant_driver: string;
  albedo: number;
  fvc: number;
  building_density: number;
  sky_view_factor: number;
  severity_level: 'moderate' | 'high' | 'critical';
}

export interface HotspotFeature {
  type: 'Feature';
  geometry: {
    type: 'Polygon';
    coordinates: number[][][];
  };
  properties: HotspotProperties;
}

export interface HotspotFeatureCollection {
  type: 'FeatureCollection';
  features: HotspotFeature[];
  metadata: {
    regional_mean_lst_celsius: number;
    regional_std_lst_celsius: number;
    max_lst_celsius: number;
    hotspot_count: number;
    sensor: string;
    date_range: string;
  };
}

export interface SimulationResult {
  scenario_id: string;
  scenario_name: string;
  status: string;
  strategy_type: string;
  budget_spent_usd: number;
  total_area_modified_m2: number;
  mean_lst_reduction_celsius: number;
  max_lst_reduction_celsius: number;
  annual_cooling_energy_saved_kwh: number;
  annual_co2_avoided_tons: number;
  payback_period_years: number;
  utci_thermal_stress_category_shift: string;
}

export interface AllocatedParcel {
  parcel_index: number;
  grid_x: number;
  grid_y: number;
  approx_lon: number;
  approx_lat: number;
  intervention_type: string;
  area_m2: number;
  cost_usd: number;
  expected_delta_t_celsius: number;
  heat_vulnerability_score: number;
  priority_rank: number;
}

export interface ParetoPoint {
  budget_usd: number;
  spent_usd: number;
  area_m2: number;
  mean_cooling_celsius: number;
  max_cooling_celsius: number;
  parcels_allocated: number;
}

export interface ParetoResponse {
  frontier_points: ParetoPoint[];
  knee_point_recommended_budget_usd: number;
  metadata: Record<string, any>;
}

export interface CityPreset {
  id: string;
  name: string;
  state: string;
  bbox: [number, number, number, number];
  center: [number, number];
  description: string;
  climateZone: string;
}

export type UserRole = 'customer' | 'admin';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization?: string | null;
  is_active: boolean;
  created_at?: string | null;
  last_login_at?: string | null;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface TelemetryLogItem {
  id: string;
  endpoint: string;
  method: string;
  status_code: number;
  duration_ms: number;
  user_id?: string | null;
  user_role: string;
  ip_address?: string | null;
  user_agent?: string | null;
  error_message?: string | null;
  timestamp: string;
}

export interface TelemetrySummary {
  total_requests: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  error_rate_percent: number;
  cache_hit_ratio_percent: number;
  active_sessions: number;
  status_breakdown: Record<string, number>;
  endpoint_distribution: Record<string, number>;
  server_uptime_hours: number;
  system_status: string;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  cpu_usage_percent: number;
  memory_usage_mb: number;
  database_connected: boolean;
  redis_connected: boolean;
  pinn_engine_device: string;
  satellite_providers: Record<string, string>;
}
