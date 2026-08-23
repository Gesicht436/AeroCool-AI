"""Pydantic Request and Response Schemas for API Serialization."""

from aerocool_ai.backend_api.schemas.hotspot_schema import (
    HotspotDetectionRequest,
    HotspotFeature,
    HotspotFeatureCollection,
    HotspotProperties,
)
from aerocool_ai.backend_api.schemas.optimization_response import (
    AllocatedParcelSchema,
    OptimizationAllocationRequest,
    OptimizationAllocationResponse,
    ParetoFrontierResponse,
    ParetoPointSchema,
)
from aerocool_ai.backend_api.schemas.scenario_request import (
    ScenarioItemResponse,
    SimulationRunRequest,
    SimulationRunResponse,
)

__all__ = [
    "HotspotDetectionRequest",
    "HotspotProperties",
    "HotspotFeature",
    "HotspotFeatureCollection",
    "SimulationRunRequest",
    "SimulationRunResponse",
    "ScenarioItemResponse",
    "OptimizationAllocationRequest",
    "AllocatedParcelSchema",
    "OptimizationAllocationResponse",
    "ParetoPointSchema",
    "ParetoFrontierResponse",
]
