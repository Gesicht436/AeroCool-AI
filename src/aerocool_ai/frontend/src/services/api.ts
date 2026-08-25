import {
  AuthTokenResponse,
  HotspotFeatureCollection,
  ParetoResponse,
  SimulationResult,
  SystemHealth,
  TelemetryLogItem,
  TelemetrySummary,
  UserProfile,
} from '../types';

const API_BASE = '/api/v1';

function getAuthHeaders(token?: string | null): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const activeToken = token || localStorage.getItem('aerocool_token');
  if (activeToken) {
    headers['Authorization'] = `Bearer ${activeToken}`;
  }
  return headers;
}

// ----------------------------------------------------
// Geospatial & Physics Endpoints
// ----------------------------------------------------

export async function fetchHotspots(
  bbox: [number, number, number, number],
  minAnomaly: number = 2.0
): Promise<HotspotFeatureCollection> {
  const res = await fetch(`${API_BASE}/hotspots/detect`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      bbox,
      start_date: '2026-05-01',
      end_date: '2026-06-30',
      min_temp_anomaly_celsius: minAnomaly,
      resolution_meters: 30.0,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch hotspots: ${res.statusText}`);
  }
  return res.json();
}

export async function runSimulation(
  bbox: [number, number, number, number],
  strategyType: string,
  targetCoverage: number,
  budgetUsd: number
): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/simulation/run`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      scenario_name: `Intervention-${strategyType.toUpperCase()}`,
      bbox,
      strategy_type: strategyType,
      target_coverage_fraction: targetCoverage,
      budget_usd: budgetUsd,
    }),
  });
  if (!res.ok) {
    throw new Error(`Simulation failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchParetoFrontier(
  bbox: [number, number, number, number],
  budgetUsd: number
): Promise<ParetoResponse> {
  const res = await fetch(`${API_BASE}/optimization/pareto`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      bbox,
      budget_usd: budgetUsd,
      candidate_strategies: ['green_roof', 'cool_roof', 'urban_canopy', 'cool_pavement'],
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to compute Pareto curve: ${res.statusText}`);
  }
  return res.json();
}

// ----------------------------------------------------
// Authentication Endpoints
// ----------------------------------------------------

export async function loginUser(email: string, password: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Login failed.');
  }
  return res.json();
}

export async function registerUser(
  email: string,
  password: string,
  fullName: string,
  role: string = 'customer',
  organization?: string
): Promise<AuthTokenResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, full_name: fullName, role, organization }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Registration failed.');
  }
  return res.json();
}

export async function demoLogin(role: 'admin' | 'customer'): Promise<AuthTokenResponse> {
  const res = await fetch(`${API_BASE}/auth/demo-login/${role}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Demo login failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchMyProfile(token?: string): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    throw new Error('Failed to fetch user profile.');
  }
  return res.json();
}

// ----------------------------------------------------
// Admin & Telemetry Endpoints
// ----------------------------------------------------

export async function fetchTelemetrySummary(token?: string): Promise<TelemetrySummary> {
  const res = await fetch(`${API_BASE}/admin/telemetry`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch telemetry summary: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTelemetryLogs(token?: string, limit: number = 50): Promise<TelemetryLogItem[]> {
  const res = await fetch(`${API_BASE}/admin/telemetry/logs?limit=${limit}`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch telemetry logs: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchUsersList(token?: string): Promise<{ users: UserProfile[]; total: number }> {
  const res = await fetch(`${API_BASE}/admin/users`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch users list: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSystemHealth(token?: string): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/admin/health`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch system health: ${res.statusText}`);
  }
  return res.json();
}
