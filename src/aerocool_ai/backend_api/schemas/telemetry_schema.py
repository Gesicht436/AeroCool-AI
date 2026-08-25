"""Pydantic v2 Schemas for System Telemetry and Diagnostics."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TelemetryEventItem(BaseModel):
    """Single API audit/telemetry event record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    user_id: Optional[str] = None
    user_role: str = "anonymous"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str


class TelemetrySummaryResponse(BaseModel):
    """Aggregated system telemetry KPIs and metrics."""

    total_requests: int = Field(..., description="Total API requests logged")
    avg_latency_ms: float = Field(..., description="Mean response latency in milliseconds")
    p95_latency_ms: float = Field(..., description="95th percentile latency in milliseconds")
    error_rate_percent: float = Field(..., description="Percentage of 4xx/5xx responses")
    cache_hit_ratio_percent: float = Field(..., description="Cache efficiency ratio")
    active_sessions: int = Field(..., description="Count of distinct active users")
    status_breakdown: Dict[str, int] = Field(..., description="HTTP status code frequency")
    endpoint_distribution: Dict[str, int] = Field(..., description="Hits per route path")
    server_uptime_hours: float = Field(..., description="Service uptime duration")
    system_status: str = Field(..., description="Overall operational health status")


class SystemHealthResponse(BaseModel):
    """Detailed live subsystem health diagnostic."""

    status: str = "operational"
    timestamp: str
    cpu_usage_percent: float = Field(..., description="CPU utilization percentage")
    memory_usage_mb: float = Field(..., description="RSS memory footprint in MB")
    database_connected: bool = Field(..., description="PostGIS connection pool status")
    redis_connected: bool = Field(..., description="Redis caching client status")
    pinn_engine_device: str = Field(..., description="Active PyTorch acceleration device")
    satellite_providers: Dict[str, str] = Field(
        default={
            "landsat_tirs": "ready",
            "ecostress_lst": "ready",
            "sentinel_lulc": "ready",
            "osm_overpass": "ready",
            "era5_meteo": "ready",
        },
        description="Status of external Earth Observation providers",
    )
