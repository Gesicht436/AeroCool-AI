"""Constrained Spatial Allocation Solver for Urban Cooling Strategies.

Solves multi-objective resource allocation:
- Maximizes heat mitigation (Delta T * Heat Vulnerability Index * Area)
- Subject to strict municipal budget limits (sum c_k * x_ik <= Budget)
- Spatial parcel suitability constraints (rooftop vs ground permeability)
- Computes Pareto efficiency curves across investment scenarios.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from aerocool_ai.core_engine.optimization.cooling_simulator import (
    CoolingInterventionSimulator,
    InterventionStrategy,
    InterventionType,
)

logger = logging.getLogger(__name__)


@dataclass
class AllocatedParcel:
    """Individual spatial cell selected for cooling intervention."""

    grid_x: int
    grid_y: int
    intervention_type: str
    area_m2: float
    cost_usd: float
    expected_delta_t_celsius: float
    heat_vulnerability_score: float
    priority_rank: int


@dataclass
class AllocationPlan:
    """Optimal spatial deployment plan within budget constraints."""

    allocated_parcels: List[AllocatedParcel]
    total_budget_usd: float
    total_spent_usd: float
    remaining_budget_usd: float
    total_area_modified_m2: float
    mean_cooling_celsius: float
    max_cooling_celsius: float
    intervention_counts: Dict[str, int]
    allocation_grid: np.ndarray  # Categorical grid mapping cell -> strategy
    metadata: Dict[str, Any]


class SpatialAllocationSolver:
    """Solves constrained spatial placement optimization for urban cooling interventions."""

    def __init__(self) -> None:
        self.simulator = CoolingInterventionSimulator()

    def solve(
        self,
        baseline_lst: np.ndarray,
        albedo_grid: np.ndarray,
        fvc_grid: np.ndarray,
        plan_area_fraction: np.ndarray,
        vulnerability_grid: Optional[np.ndarray] = None,
        budget_usd: float = 250_000.0,
        allowed_strategies: Optional[List[InterventionType]] = None,
        cell_size_m: float = 30.0,
        method: str = "greedy",
    ) -> AllocationPlan:
        """Find optimal parcel allocation maximizing heat relief under budget."""
        grid_h, grid_w = baseline_lst.shape
        cell_area_m2 = cell_size_m * cell_size_m

        if vulnerability_grid is None:
            # Default vulnerability based on temperature anomalies above mean
            mean_temp = np.mean(baseline_lst)
            vulnerability_grid = np.clip((baseline_lst - mean_temp) / 5.0, 0.1, 1.0)

        if allowed_strategies is None:
            allowed_strategies = [
                InterventionType.COOL_ROOF,
                InterventionType.GREEN_ROOF,
                InterventionType.URBAN_CANOPY,
                InterventionType.COOL_PAVEMENT,
            ]

        # Evaluate candidate interventions per cell
        candidates: List[Tuple[float, int, int, InterventionType, float, float, float]] = []

        for gy in range(grid_h):
            for gx in range(grid_w):
                bldg_density = plan_area_fraction[gy, gx]
                hvi = vulnerability_grid[gy, gx]

                # Evaluate suitable strategies for this cell
                for strat_type in allowed_strategies:
                    strategy = self.simulator.DEFAULTS[strat_type]

                    # Suitability check
                    if strat_type in [InterventionType.GREEN_ROOF, InterventionType.COOL_ROOF]:
                        if bldg_density < 0.10:
                            continue  # No rooftops
                        eligible_area = cell_area_m2 * bldg_density
                    else:
                        if bldg_density > 0.85:
                            continue  # No ground space for trees/pavement
                        eligible_area = cell_area_m2 * (1.0 - bldg_density)

                    if eligible_area < 50.0:
                        continue

                    # Cooling estimation
                    cooling_benefit = (
                        strategy.albedo_delta * 12.0
                        + strategy.fvc_delta * 4.5
                        + strategy.shading_factor * 8.0
                    )
                    cost = eligible_area * strategy.cost_per_sqm

                    # Benefit-to-Cost Ratio (Marginal Efficiency Metric)
                    weighted_benefit = cooling_benefit * hvi * eligible_area
                    marginal_roi = weighted_benefit / max(cost, 1.0)

                    candidates.append((
                        marginal_roi,
                        gx,
                        gy,
                        strat_type,
                        eligible_area,
                        cost,
                        cooling_benefit,
                    ))

        # Sort candidates descending by marginal ROI
        candidates.sort(key=lambda x: x[0], reverse=True)

        allocated: List[AllocatedParcel] = []
        allocated_cells = set()
        total_spent = 0.0
        allocation_grid = np.full((grid_h, grid_w), -1, dtype=np.int32)
        intervention_counts: Dict[str, int] = {st.value: 0 for st in allowed_strategies}
        strat_to_code = {st: i for i, st in enumerate(allowed_strategies)}

        if method == "milp" and len(candidates) > 0:
            try:
                from scipy.optimize import Bounds, LinearConstraint, milp

                n_cand = len(candidates)
                # Objective: minimize -weighted_benefit to maximize total relief
                c_obj = np.array([-cand[0] * cand[5] for cand in candidates])
                costs = np.array([cand[5] for cand in candidates])

                # Budget constraint: sum(cost_i * x_i) <= budget
                A_budget = costs.reshape(1, -1)
                constraints = [LinearConstraint(A_budget, lb=0, ub=budget_usd)]

                # Cell exclusivity constraint: at most 1 intervention per (gx, gy)
                cell_map: Dict[Tuple[int, int], List[int]] = {}
                for idx, cand in enumerate(candidates):
                    key = (cand[1], cand[2])
                    cell_map.setdefault(key, []).append(idx)

                multicell_keys = [k for k, v in cell_map.items() if len(v) > 1]
                if multicell_keys:
                    A_excl = np.zeros((len(multicell_keys), n_cand))
                    for r_idx, k in enumerate(multicell_keys):
                        for c_idx in cell_map[k]:
                            A_excl[r_idx, c_idx] = 1.0
                    constraints.append(LinearConstraint(A_excl, lb=0, ub=1.0))

                integrality = np.ones(n_cand)
                bounds = Bounds(lb=0, ub=1)

                res = milp(c=c_obj, integrality=integrality, constraints=constraints, bounds=bounds)
                if res.success and res.x is not None:
                    selected_indices = np.where(res.x > 0.5)[0]
                    for rank, idx in enumerate(selected_indices, 1):
                        roi, gx, gy, st_type, area_m2, cost, delta_t = candidates[idx]
                        total_spent += cost
                        allocated_cells.add((gx, gy))
                        allocation_grid[gy, gx] = strat_to_code[st_type]
                        intervention_counts[st_type.value] += 1
                        allocated.append(
                            AllocatedParcel(
                                grid_x=gx,
                                grid_y=gy,
                                intervention_type=st_type.value,
                                area_m2=float(area_m2),
                                cost_usd=float(cost),
                                expected_delta_t_celsius=float(delta_t),
                                heat_vulnerability_score=float(vulnerability_grid[gy, gx]),
                                priority_rank=rank,
                            )
                        )
            except Exception as exc:
                logger.warning(f"MILP solver fallback to greedy knapsack: {exc}")

        # Fallback to greedy knapsack if MILP was not requested or produced empty
        if not allocated:
            for rank, (roi, gx, gy, st_type, area_m2, cost, delta_t) in enumerate(candidates, 1):
                if (gx, gy) in allocated_cells:
                    continue  # Parcel already assigned an intervention

                if total_spent + cost <= budget_usd:
                    total_spent += cost
                    allocated_cells.add((gx, gy))
                    allocation_grid[gy, gx] = strat_to_code[st_type]
                    intervention_counts[st_type.value] += 1

                    allocated.append(
                        AllocatedParcel(
                            grid_x=gx,
                            grid_y=gy,
                            intervention_type=st_type.value,
                            area_m2=float(area_m2),
                            cost_usd=float(cost),
                            expected_delta_t_celsius=float(delta_t),
                            heat_vulnerability_score=float(vulnerability_grid[gy, gx]),
                            priority_rank=rank,
                        )
                    )

        total_area = sum(p.area_m2 for p in allocated)
        mean_cooling = float(np.mean([p.expected_delta_t_celsius for p in allocated])) if allocated else 0.0
        max_cooling = float(np.max([p.expected_delta_t_celsius for p in allocated])) if allocated else 0.0

        return AllocationPlan(
            allocated_parcels=allocated,
            total_budget_usd=budget_usd,
            total_spent_usd=total_spent,
            remaining_budget_usd=budget_usd - total_spent,
            total_area_modified_m2=total_area,
            mean_cooling_celsius=mean_cooling,
            max_cooling_celsius=max_cooling,
            intervention_counts=intervention_counts,
            allocation_grid=allocation_grid,
            metadata={
                "allocated_count": len(allocated),
                "budget_utilization_pct": (total_spent / max(budget_usd, 1.0)) * 100.0,
            },
        )

    def generate_pareto_frontier(
        self,
        baseline_lst: np.ndarray,
        albedo_grid: np.ndarray,
        fvc_grid: np.ndarray,
        plan_area_fraction: np.ndarray,
        vulnerability_grid: Optional[np.ndarray] = None,
        budget_steps: Optional[List[float]] = None,
    ) -> List[Dict[str, float]]:
        """Generate Pareto efficiency frontier over different budget thresholds."""
        if budget_steps is None:
            budget_steps = [50_000, 100_000, 250_000, 500_000, 1_000_000, 2_000_000]

        frontier = []
        for b in budget_steps:
            plan = self.solve(
                baseline_lst=baseline_lst,
                albedo_grid=albedo_grid,
                fvc_grid=fvc_grid,
                plan_area_fraction=plan_area_fraction,
                vulnerability_grid=vulnerability_grid,
                budget_usd=b,
            )
            frontier.append({
                "budget_usd": b,
                "spent_usd": plan.total_spent_usd,
                "area_m2": plan.total_area_modified_m2,
                "mean_cooling_celsius": plan.mean_cooling_celsius,
                "max_cooling_celsius": plan.max_cooling_celsius,
                "parcels_allocated": len(plan.allocated_parcels),
            })

        return frontier
