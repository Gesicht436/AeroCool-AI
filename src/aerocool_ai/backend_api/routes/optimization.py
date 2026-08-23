"""Spatial Intervention Optimization and Strategy Allocation Endpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
import numpy as np

from aerocool_ai.backend_api.dependencies import get_app_settings, get_redis_client
from aerocool_ai.backend_api.schemas.optimization_response import (
    AllocatedParcelSchema,
    OptimizationAllocationRequest,
    OptimizationAllocationResponse,
    ParetoFrontierResponse,
    ParetoPointSchema,
)
from aerocool_ai.config import Settings
from aerocool_ai.core_engine.ingestion.gee_landsat_collector import LandsatLSTCollector
from aerocool_ai.core_engine.ingestion.osm_morphology_collector import OSMMorphologyCollector
from aerocool_ai.core_engine.ingestion.sentinel_lulc_collector import SentinelLULCCollector
from aerocool_ai.core_engine.optimization.cooling_simulator import InterventionType
from aerocool_ai.core_engine.optimization.spatial_allocator import SpatialAllocationSolver
from aerocool_ai.core_engine.preprocessing.feature_extractor import UrbanFeatureExtractor

router = APIRouter(prefix="/optimization", tags=["Spatial Optimization"])
logger = logging.getLogger(__name__)


@router.post(
    "/allocate",
    response_model=OptimizationAllocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Solve Optimal Spatial Intervention Placement",
)
async def allocate_cooling_interventions(
    payload: OptimizationAllocationRequest,
    settings: Settings = Depends(get_app_settings),
) -> OptimizationAllocationResponse:
    """Solve constrained multi-objective spatial allocation of cooling interventions under budget."""
    try:
        bbox = payload.bbox
        min_lon, min_lat, max_lon, max_lat = bbox

        # 1. Fetch satellite and morphology base data
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

        # 2. Solve constrained optimization
        solver = SpatialAllocationSolver()
        allowed = [InterventionType(s) for s in payload.allowed_strategies]

        plan = solver.solve(
            baseline_lst=lst_res.data,
            albedo_grid=feat_set.albedo,
            fvc_grid=feat_set.fvc,
            plan_area_fraction=morph_res.plan_area_fraction,
            budget_usd=payload.budget_usd,
            allowed_strategies=allowed,
        )

        grid_h, grid_w = lst_res.data.shape
        lon_step = (max_lon - min_lon) / grid_w
        lat_step = (max_lat - min_lat) / grid_h

        allocated_schemas: List[AllocatedParcelSchema] = []
        geojson_features = []

        for idx, p in enumerate(plan.allocated_parcels):
            c_lon = float(min_lon + (p.grid_x + 0.5) * lon_step)
            c_lat = float(max_lat - (p.grid_y + 0.5) * lat_step)

            allocated_schemas.append(
                AllocatedParcelSchema(
                    parcel_index=int(idx),
                    grid_x=int(p.grid_x),
                    grid_y=int(p.grid_y),
                    approx_lon=round(c_lon, 5),
                    approx_lat=round(c_lat, 5),
                    intervention_type=str(p.intervention_type),
                    area_m2=round(float(p.area_m2), 1),
                    cost_usd=round(float(p.cost_usd), 2),
                    expected_delta_t_celsius=round(float(p.expected_delta_t_celsius), 2),
                    heat_vulnerability_score=round(float(p.heat_vulnerability_score), 2),
                    priority_rank=int(p.priority_rank),
                )
            )

            geojson_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(c_lon, 5), round(c_lat, 5)],
                },
                "properties": {
                    "intervention": str(p.intervention_type),
                    "cost_usd": round(float(p.cost_usd), 2),
                    "cooling_celsius": round(float(p.expected_delta_t_celsius), 2),
                    "priority": int(p.priority_rank),
                },
            })

        geojson_allocation = {
            "type": "FeatureCollection",
            "features": geojson_features,
        }

        # Convert plan metadata to pure python primitives
        clean_metadata = {k: float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v for k, v in plan.metadata.items()}

        return OptimizationAllocationResponse(
            total_budget_usd=round(float(plan.total_budget_usd), 2),
            total_spent_usd=round(float(plan.total_spent_usd), 2),
            remaining_budget_usd=round(float(plan.remaining_budget_usd), 2),
            total_area_modified_m2=round(float(plan.total_area_modified_m2), 1),
            mean_cooling_celsius=round(float(plan.mean_cooling_celsius), 2),
            max_cooling_celsius=round(float(plan.max_cooling_celsius), 2),
            intervention_counts={str(k): int(v) for k, v in plan.intervention_counts.items()},
            allocated_parcels=allocated_schemas,
            geojson_allocation=geojson_allocation,
            metadata=clean_metadata,
        )

    except Exception as exc:
        logger.error(f"Optimization allocation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spatial optimization failed: {str(exc)}",
        )


@router.post(
    "/pareto",
    response_model=ParetoFrontierResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Multi-Budget Pareto Efficiency Frontier",
)
async def compute_pareto_frontier(
    payload: OptimizationAllocationRequest,
    settings: Settings = Depends(get_app_settings),
    cache: Any = Depends(get_redis_client),
) -> ParetoFrontierResponse:
    """Generate Pareto efficiency curve between investment cost and temperature relief."""
    try:
        cache_key = f"pareto:{payload.bbox}:{payload.budget_usd}"
        cached = await cache.get(cache_key)
        if cached:
            return ParetoFrontierResponse.model_validate_json(cached)

        bbox = payload.bbox

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
            red=opt_red if (opt_red := opt_res.red) is not None else opt_res.blue,
            nir=opt_res.nir,
            swir1=opt_res.swir1,
            swir2=opt_res.swir2,
            building_height=morph_res.building_height_mean,
            plan_area_fraction=morph_res.plan_area_fraction,
        )

        solver = SpatialAllocationSolver()
        raw_frontier = solver.generate_pareto_frontier(
            baseline_lst=lst_res.data,
            albedo_grid=feat_set.albedo,
            fvc_grid=feat_set.fvc,
            plan_area_fraction=morph_res.plan_area_fraction,
        )

        points = [
            ParetoPointSchema(
                budget_usd=float(pt["budget_usd"]),
                spent_usd=round(float(pt["spent_usd"]), 2),
                area_m2=round(float(pt["area_m2"]), 1),
                mean_cooling_celsius=round(float(pt["mean_cooling_celsius"]), 2),
                max_cooling_celsius=round(float(pt["max_cooling_celsius"]), 2),
                parcels_allocated=int(pt["parcels_allocated"]),
            )
            for pt in raw_frontier
        ]

        # Recommend knee point (~ middle inflection budget)
        recommended_budget = float(raw_frontier[min(2, len(raw_frontier) - 1)]["budget_usd"])

        response = ParetoFrontierResponse(
            frontier_points=points,
            knee_point_recommended_budget_usd=recommended_budget,
            metadata={"num_scenarios_evaluated": len(points)},
        )

        try:
            await cache.set(cache_key, response.model_dump_json(), ex=300)
        except Exception as cache_err:
            logger.debug(f"Cache write skipped: {cache_err}")

        return response

    except Exception as exc:
        logger.error(f"Pareto frontier calculation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pareto analysis failed: {str(exc)}",
        )
