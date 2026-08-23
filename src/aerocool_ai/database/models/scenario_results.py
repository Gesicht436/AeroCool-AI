"""Simulation Scenario and Optimization Results Persistence Models.

Tracks user-defined urban cooling simulations, optimization runs, and impact logs in PostGIS.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aerocool_ai.database.connection import Base


class SimulationScenario(Base):
    """Simulation run configuration and lifecycle state."""

    __tablename__ = "simulation_scenarios"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scenario_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Target spatial boundary polygon for intervention simulation
    boundary_geom: Mapped[Optional[Any]] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )

    strategy_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="multi_strategy"
    )
    budget_usd: Mapped[float] = mapped_column(Float, default=250_000.0)
    target_area_fraction: Mapped[float] = mapped_column(Float, default=0.50)

    status: Mapped[str] = mapped_column(
        String(30), default="pending", index=True
    )  # "pending", "running", "completed", "failed"
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    results: Mapped[List["ScenarioResultRecord"]] = relationship(
        "ScenarioResultRecord", back_populates="scenario", cascade="all, delete-orphan"
    )


class ScenarioResultRecord(Base):
    """Computed thermodynamic outcomes and spatial impact records."""

    __tablename__ = "scenario_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scenario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("simulation_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mean_lst_reduction_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    max_lst_reduction_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    mean_air_temp_reduction_celsius: Mapped[float] = mapped_column(Float, nullable=False)

    total_area_modified_m2: Mapped[float] = mapped_column(Float, nullable=False)
    total_spent_usd: Mapped[float] = mapped_column(Float, nullable=False)

    annual_cooling_energy_saved_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    annual_co2_avoided_tons: Mapped[float] = mapped_column(Float, default=0.0)
    payback_period_years: Mapped[float] = mapped_column(Float, default=0.0)

    # GeoJSON representation of allocated parcels and temperature deltas
    result_geojson: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    raster_artifact_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    scenario: Mapped["SimulationScenario"] = relationship(
        "SimulationScenario", back_populates="results"
    )
