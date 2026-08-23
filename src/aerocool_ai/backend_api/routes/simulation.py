"""Urban Cooling Simulation Endpoints."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from aerocool_ai.backend_api.dependencies import get_app_settings, get_db
from aerocool_ai.backend_api.schemas.scenario_request import (
    ScenarioItemResponse,
    SimulationRunRequest,
    SimulationRunResponse,
)
from aerocool_ai.config import Settings
from aerocool_ai.core_engine.ingestion.gee_landsat_collector import LandsatLSTCollector
from aerocool_ai.core_engine.ingestion.osm_morphology_collector import OSMMorphologyCollector
from aerocool_ai.core_engine.ingestion.sentinel_lulc_collector import SentinelLULCCollector
from aerocool_ai.core_engine.optimization.cooling_simulator import (
    CoolingInterventionSimulator,
    InterventionStrategy,
    InterventionType,
)
from aerocool_ai.core_engine.optimization.impact_evaluator import ImpactEvaluator
from aerocool_ai.core_engine.preprocessing.feature_extractor import UrbanFeatureExtractor
from aerocool_ai.database.repositories.scenario_repository import ScenarioRepository

router = APIRouter(prefix="/simulation", tags=["Cooling Simulation"])
logger = logging.getLogger(__name__)


@router.post(
    "/run",
    response_model=SimulationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Urban Cooling Intervention Simulation",
)
async def run_cooling_simulation(
    payload: SimulationRunRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> SimulationRunResponse:
    """Simulate the thermodynamic cooling impact of spatial urban interventions."""
    try:
        scenario_repo = ScenarioRepository(db)
        # Create pending scenario entry in DB
        db_scenario = await scenario_repo.create_scenario(
            scenario_name=payload.scenario_name,
            strategy_type=payload.strategy_type,
            budget_usd=payload.budget_usd,
            target_area_fraction=payload.target_area_fraction,
            description=payload.description,
            boundary_bbox=payload.bbox,
        )

        bbox = payload.bbox
        # 1. Fetch baseline layers
        lst_collector = LandsatLSTCollector(settings)
        lst_res = lst_collector.fetch_lst_aoi(bbox, "2026-06-01", "2026-08-31")

        sentinel_col = SentinelLULCCollector(settings)
        opt_res = sentinel_col.fetch_multispectral_and_lulc(bbox, "2026-06-01", "2026-08-31")

        morph_col = OSMMorphologyCollector(settings)
        morph_res = morph_col.fetch_morphology(bbox, grid_shape=lst_res.data.shape)

        extractor = UrbanFeatureExtractor()
        feat_set = extractor.extract_features(
            blue=opt_res.blue,
            green=opt_res.green,
            red=opt_res.red,
            nir=opt_res.nir,
            swir1=opt_res.swir1,
            swir2=opt_res.swir2,
            building_height=morph_res.building_height_mean,
            plan_area_fraction=morph_res.plan_area_fraction,
        )

        # 2. Configure strategy
        simulator = CoolingInterventionSimulator()
        strategy_type_enum = (
            InterventionType(payload.strategy_type)
            if payload.strategy_type != "multi_strategy"
            else InterventionType.GREEN_ROOF
        )
        base_strategy = simulator.DEFAULTS[strategy_type_enum]

        strategy = InterventionStrategy(
            intervention_type=strategy_type_enum,
            target_area_fraction=payload.target_area_fraction,
            albedo_delta=(
                payload.custom_albedo_delta
                if payload.custom_albedo_delta is not None
                else base_strategy.albedo_delta
            ),
            fvc_delta=(
                payload.custom_fvc_delta
                if payload.custom_fvc_delta is not None
                else base_strategy.fvc_delta
            ),
            cost_per_sqm=base_strategy.cost_per_sqm,
            shading_factor=base_strategy.shading_factor,
            evaporative_efficiency=base_strategy.evaporative_efficiency,
        )

        # 3. Simulate cooling
        sim_res = simulator.simulate(
            baseline_lst=lst_res.data,
            albedo_grid=feat_set.albedo,
            fvc_grid=feat_set.fvc,
            plan_area_fraction=morph_res.plan_area_fraction,
            strategy=strategy,
        )

        # Cap by budget
        if sim_res.estimated_cost_usd > payload.budget_usd:
            scaling_factor = payload.budget_usd / sim_res.estimated_cost_usd
            sim_res.total_area_modified_m2 *= scaling_factor
            sim_res.estimated_cost_usd = payload.budget_usd
            sim_res.delta_lst *= scaling_factor
            sim_res.mitigated_lst = sim_res.baseline_lst - sim_res.delta_lst
            sim_res.mean_cooling_celsius *= scaling_factor
            sim_res.max_cooling_celsius *= scaling_factor

        # 4. Evaluate impact
        evaluator = ImpactEvaluator()
        impact = evaluator.evaluate(
            baseline_lst=sim_res.baseline_lst,
            mitigated_lst=sim_res.mitigated_lst,
            modified_area_m2=sim_res.total_area_modified_m2,
            capital_investment_usd=sim_res.estimated_cost_usd,
        )

        # 5. Format GeoJSON
        min_lon, min_lat, max_lon, max_lat = bbox
        grid_h, grid_w = sim_res.delta_lst.shape
        lon_step = (max_lon - min_lon) / grid_w
        lat_step = (max_lat - min_lat) / grid_h

        sample_features = []
        active_indices = np.argwhere(sim_res.intervention_mask)[:30]
        for gy, gx in active_indices:
            c_lon = min_lon + (gx + 0.5) * lon_step
            c_lat = max_lat - (gy + 0.5) * lat_step
            dt = float(sim_res.delta_lst[gy, gx])
            sample_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(c_lon, 5), round(c_lat, 5)],
                },
                "properties": {
                    "delta_t_celsius": round(dt, 2),
                    "intervention": strategy.intervention_type.value,
                },
            })

        result_geojson = {
            "type": "FeatureCollection",
            "features": sample_features,
        }

        # 6. Update scenario in database
        await scenario_repo.update_scenario_status(db_scenario.id, "completed")
        await scenario_repo.record_scenario_result(
            scenario_id=db_scenario.id,
            mean_lst_reduction=impact.mean_lst_reduction_celsius,
            max_lst_reduction=impact.max_lst_reduction_celsius,
            mean_air_temp_reduction=impact.mean_air_temp_reduction_celsius,
            total_area_modified_m2=sim_res.total_area_modified_m2,
            total_spent_usd=sim_res.estimated_cost_usd,
            annual_energy_saved_kwh=impact.annual_cooling_energy_saved_kwh,
            annual_co2_avoided_tons=impact.annual_co2_avoided_tons,
            payback_period_years=impact.payback_period_years,
            result_geojson=result_geojson,
        )

        return SimulationRunResponse(
            scenario_id=db_scenario.id,
            scenario_name=payload.scenario_name,
            strategy_type=payload.strategy_type,
            status="completed",
            mean_lst_reduction_celsius=round(impact.mean_lst_reduction_celsius, 2),
            max_lst_reduction_celsius=round(impact.max_lst_reduction_celsius, 2),
            mean_air_temp_reduction_celsius=round(impact.mean_air_temp_reduction_celsius, 2),
            total_area_modified_m2=round(sim_res.total_area_modified_m2, 1),
            total_spent_usd=round(sim_res.estimated_cost_usd, 2),
            annual_cooling_energy_saved_kwh=round(impact.annual_cooling_energy_saved_kwh, 1),
            annual_co2_avoided_tons=round(impact.annual_co2_avoided_tons, 2),
            payback_period_years=round(impact.payback_period_years, 1),
            utci_thermal_stress_category_shift=impact.utci_thermal_stress_category_shift,
            result_geojson=result_geojson,
            metadata={"cells_modified": int(np.sum(sim_res.intervention_mask))},
        )

    except Exception as exc:
        logger.error(f"Simulation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation run failed: {str(exc)}",
        )


@router.get(
    "/{scenario_id}",
    response_model=Dict[str, Any],
    summary="Get Simulation Scenario Details",
)
async def get_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve detailed scenario metadata and execution results from database."""
    repo = ScenarioRepository(db)
    scenario = await repo.get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID '{scenario_id}' not found.",
        )

    results_data = []
    for res in scenario.results:
        results_data.append({
            "mean_lst_reduction_celsius": res.mean_lst_reduction_celsius,
            "max_lst_reduction_celsius": res.max_lst_reduction_celsius,
            "mean_air_temp_reduction_celsius": res.mean_air_temp_reduction_celsius,
            "total_area_modified_m2": res.total_area_modified_m2,
            "total_spent_usd": res.total_spent_usd,
            "annual_cooling_energy_saved_kwh": res.annual_cooling_energy_saved_kwh,
            "annual_co2_avoided_tons": res.annual_co2_avoided_tons,
            "payback_period_years": res.payback_period_years,
            "result_geojson": res.result_geojson,
        })

    return {
        "scenario_id": scenario.id,
        "scenario_name": scenario.scenario_name,
        "strategy_type": scenario.strategy_type,
        "budget_usd": scenario.budget_usd,
        "status": scenario.status,
        "created_at": str(scenario.created_at),
        "results": results_data,
    }


@router.get(
    "",
    response_model=List[ScenarioItemResponse],
    summary="List Simulation Scenarios",
)
async def list_scenarios(
    status: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[ScenarioItemResponse]:
    """List historical simulation runs with pagination."""
    repo = ScenarioRepository(db)
    scenarios = await repo.list_scenarios(status=status, limit=limit, offset=offset)

    return [
        ScenarioItemResponse(
            scenario_id=s.id,
            scenario_name=s.scenario_name,
            strategy_type=s.strategy_type,
            budget_usd=s.budget_usd,
            status=s.status,
            created_at=str(s.created_at),
        )
        for s in scenarios
    ]
