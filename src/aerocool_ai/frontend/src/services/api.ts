import { HotspotFeatureCollection, SimulationResult, OptimizationResponse, ParetoResponse } from '../types';

const API_BASE = '/api/v1';

export async function fetchHotspots(bbox: [number, number, number, number], minAnomaly: number = 2.0): Promise<HotspotFeatureCollection> {
  const res = await fetch(`${API_BASE}/hotspots/detect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bbox,
      start_date: '2026-05-01',
      end_date: '2026-06-30',
      min_temp_anomaly_celsius: minAnomaly,
      sensor: 'landsat_8',
    }),
  });

  if (!res.ok) {
    throw new Error(`Hotspot detection failed: ${res.statusText}`);
  }
  return res.json();
}

export async function runSimulation(
  bbox: [number, number, number, number],
  strategyType: string,
  targetFraction: number,
  budgetUsd: number
): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/simulation/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario_name: `Scenario-${strategyType}-${Date.now().toString().slice(-4)}`,
      bbox,
      strategy_type: strategyType,
      target_coverage_pct: targetFraction * 100.0,
      budget_usd: budgetUsd,
    }),
  });

  if (!res.ok) {
    throw new Error(`Simulation failed: ${res.statusText}`);
  }
  return res.json();
}

export async function runOptimization(
  bbox: [number, number, number, number],
  budgetUsd: number,
  allowedStrategies: string[]
): Promise<OptimizationResponse> {
  const res = await fetch(`${API_BASE}/optimization/allocate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bbox,
      budget_usd: budgetUsd,
      allowed_strategies: allowedStrategies,
    }),
  });

  if (!res.ok) {
    throw new Error(`Optimization failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchParetoFrontier(
  bbox: [number, number, number, number],
  budgetUsd: number
): Promise<ParetoResponse> {
  const res = await fetch(`${API_BASE}/optimization/pareto`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bbox,
      budget_usd: budgetUsd,
    }),
  });

  if (!res.ok) {
    throw new Error(`Pareto calculation failed: ${res.statusText}`);
  }
  return res.json();
}
