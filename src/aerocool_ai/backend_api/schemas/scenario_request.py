"""Simulation Scenario Request and Response Schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class SimulationRunRequest(BaseModel):
    """Payload to trigger parametric cooling scenario simulation."""

    scenario_name: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Descriptive identifier for the scenario run",
        examples=["Downtown Core Green & Cool Roof Initiative"],
    )
    description: Optional[str] = Field(
        default=None, description="Detailed project description or planning notes"
    )
    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Spatial boundary [min_lon, min_lat, max_lon, max_lat]",
        examples=[(-74.02, 40.70, -73.95, 40.78)],
    )
    strategy_type: Literal[
        "green_roof",
        "cool_roof",
        "urban_canopy",
        "cool_pavement",
        "permeable_pavement",
        "multi_strategy",
    ] = Field(default="green_roof", description="Primary urban cooling intervention strategy")
    target_area_fraction: float = Field(
        default=0.60,
        ge=0.05,
        le=1.0,
        description="Fraction of eligible surface area to convert",
    )
    budget_usd: float = Field(
        default=250_000.0,
        ge=1000.0,
        description="Total municipal capital expenditure budget in USD",
    )
    custom_albedo_delta: Optional[float] = Field(
        default=None, ge=0.0, le=0.9, description="Override default albedo shift"
    )
    custom_fvc_delta: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Override default vegetation fraction shift"
    )


class SimulationRunResponse(BaseModel):
    """Output payload summarizing thermodynamic cooling impact and economic metrics."""

    scenario_id: str
    scenario_name: str
    strategy_type: str
    status: str
    mean_lst_reduction_celsius: float
    max_lst_reduction_celsius: float
    mean_air_temp_reduction_celsius: float
    total_area_modified_m2: float
    total_spent_usd: float
    annual_cooling_energy_saved_kwh: float
    annual_co2_avoided_tons: float
    payback_period_years: float
    utci_thermal_stress_category_shift: str
    result_geojson: Dict[str, Any]
    metadata: Dict[str, Any]


class ScenarioItemResponse(BaseModel):
    """Brief scenario summary for listing endpoints."""

    scenario_id: str
    scenario_name: str
    strategy_type: str
    budget_usd: float
    status: str
    created_at: str
