"""GeoJSON Heat Stress and Urban Heat Island (UHI) Hotspot Schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class HotspotDetectionRequest(BaseModel):
    """Payload to trigger UHI hotspot detection over an Area of Interest (AOI)."""

    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Bounding box coordinates [min_lon, min_lat, max_lon, max_lat]",
        examples=[(-74.02, 40.70, -73.95, 40.78)],
    )
    start_date: str = Field(
        default="2026-06-01", description="Observation start date (YYYY-MM-DD)"
    )
    end_date: str = Field(
        default="2026-08-31", description="Observation end date (YYYY-MM-DD)"
    )
    sensor: Literal["Landsat-8/9", "ECOSTRESS", "Sentinel-2", "Composite"] = Field(
        default="Landsat-8/9", description="Primary thermal remote sensing platform"
    )
    min_temp_anomaly_celsius: float = Field(
        default=2.5,
        ge=0.5,
        le=15.0,
        description="Minimum temperature anomaly above regional background to classify as hotspot",
    )
    resolution_meters: int = Field(
        default=30,
        ge=10,
        le=100,
        description="Target spatial grid resolution in meters",
    )


class GeoJSONGeometry(BaseModel):
    """GeoJSON Polygon / Point geometry definition."""

    type: Literal["Point", "Polygon", "MultiPolygon"] = "Polygon"
    coordinates: List[Any]


class HotspotProperties(BaseModel):
    """Thermal attributes and microclimate drivers for a single hotspot."""

    hotspot_id: str
    lst_celsius: float
    uhi_intensity_celsius: float
    regional_mean_lst: float
    heat_vulnerability_index: float  # [0.0 - 1.0]
    dominant_driver: str  # e.g. "Low Albedo Roofs", "Vegetation Deficit", "High Building Density"
    albedo: float
    fvc: float
    building_density: float
    sky_view_factor: float
    severity_level: Literal["Low", "Moderate", "High", "Critical", "Extreme"]


class HotspotFeature(BaseModel):
    """Standard RFC 7946 GeoJSON Feature."""

    type: Literal["Feature"] = "Feature"
    geometry: GeoJSONGeometry
    properties: HotspotProperties


class HotspotFeatureCollection(BaseModel):
    """Standard RFC 7946 GeoJSON FeatureCollection of detected UHI hotspots."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[HotspotFeature]
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution statistics, bounds, sensor metadata, and regional summary",
    )
