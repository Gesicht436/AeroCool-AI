"""Optimization and Spatial Allocation Schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class OptimizationAllocationRequest(BaseModel):
    """Payload to solve constrained spatial cooling intervention placement."""

    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Spatial boundary [min_lon, min_lat, max_lon, max_lat]",
        examples=[(-74.02, 40.70, -73.95, 40.78)],
    )
    budget_usd: float = Field(
        default=500_000.0,
        ge=10_000.0,
        description="Total available investment budget in USD",
    )
    allowed_strategies: List[
        Literal["green_roof", "cool_roof", "urban_canopy", "cool_pavement", "permeable_pavement"]
    ] = Field(
        default=["cool_roof", "green_roof", "urban_canopy", "cool_pavement"],
        description="Permitted intervention techniques",
    )
    prioritize_social_vulnerability: bool = Field(
        default=True,
        description="Weight placement higher in socially vulnerable, high-density residential blocks",
    )


class AllocatedParcelSchema(BaseModel):
    """Individual assigned intervention site."""

    parcel_index: int
    grid_x: int
    grid_y: int
    approx_lon: float
    approx_lat: float
    intervention_type: str
    area_m2: float
    cost_usd: float
    expected_delta_t_celsius: float
    heat_vulnerability_score: float
    priority_rank: int


class OptimizationAllocationResponse(BaseModel):
    """Optimal spatial cooling deployment results."""

    total_budget_usd: float
    total_spent_usd: float
    remaining_budget_usd: float
    total_area_modified_m2: float
    mean_cooling_celsius: float
    max_cooling_celsius: float
    intervention_counts: Dict[str, int]
    allocated_parcels: List[AllocatedParcelSchema]
    geojson_allocation: Dict[str, Any]
    metadata: Dict[str, Any]


class ParetoPointSchema(BaseModel):
    """Single scenario point on the budget-cooling Pareto frontier."""

    budget_usd: float
    spent_usd: float
    area_m2: float
    mean_cooling_celsius: float
    max_cooling_celsius: float
    parcels_allocated: int


class ParetoFrontierResponse(BaseModel):
    """Multi-budget Pareto efficiency frontier."""

    frontier_points: List[ParetoPointSchema]
    knee_point_recommended_budget_usd: float
    metadata: Dict[str, Any]
