"""Unit tests for cooling simulation, spatial allocation solver, and impact assessment."""

import numpy as np

from aerocool_ai.core_engine.optimization.cooling_simulator import (
    CoolingInterventionSimulator,
    InterventionType,
)
from aerocool_ai.core_engine.optimization.impact_evaluator import ImpactEvaluator
from aerocool_ai.core_engine.optimization.spatial_allocator import SpatialAllocationSolver


def test_cooling_simulator_green_roof():
    """Test green roof parametric thermodynamic simulation."""
    simulator = CoolingInterventionSimulator()
    strat = simulator.DEFAULTS[InterventionType.GREEN_ROOF]

    base_lst = np.full((16, 16), 36.0)
    albedo = np.full((16, 16), 0.12)
    fvc = np.full((16, 16), 0.05)
    plan_area = np.full((16, 16), 0.60)

    res = simulator.simulate(
        baseline_lst=base_lst,
        albedo_grid=albedo,
        fvc_grid=fvc,
        plan_area_fraction=plan_area,
        strategy=strat,
    )

    assert res.mean_cooling_celsius > 0.5
    assert np.all(res.mitigated_lst <= res.baseline_lst)
    assert res.estimated_cost_usd > 0


def test_spatial_allocation_solver():
    """Test budget-constrained spatial allocation solver."""
    solver = SpatialAllocationSolver()

    base_lst = np.random.uniform(32.0, 40.0, (16, 16))
    albedo = np.full((16, 16), 0.12)
    fvc = np.full((16, 16), 0.05)
    plan_area = np.full((16, 16), 0.50)

    plan = solver.solve(
        baseline_lst=base_lst,
        albedo_grid=albedo,
        fvc_grid=fvc,
        plan_area_fraction=plan_area,
        budget_usd=100_000.0,
    )

    assert plan.total_spent_usd <= 100_000.0
    assert len(plan.allocated_parcels) > 0
    assert plan.mean_cooling_celsius > 0.0


def test_impact_evaluator():
    """Test thermal comfort, avoided energy, and emission metrics."""
    evaluator = ImpactEvaluator()
    base_lst = np.full((16, 16), 37.0)
    mit_lst = np.full((16, 16), 33.5)

    report = evaluator.evaluate(
        baseline_lst=base_lst,
        mitigated_lst=mit_lst,
        modified_area_m2=50_000.0,
        capital_investment_usd=150_000.0,
    )

    assert report.mean_lst_reduction_celsius == 3.5
    assert report.mean_air_temp_reduction_celsius > 1.0
    assert report.annual_cooling_energy_saved_kwh > 0
    assert report.annual_co2_avoided_tons > 0
