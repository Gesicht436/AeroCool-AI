"""In-Situ Meteorological and Weather Sensor Observations Model.

Stores ground-truth meteorological time-series records for validation and PINN assimilation.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from aerocool_ai.database.connection import Base


class MeteoObservation(Base):
    """Ground truth time-series meteorology from weather stations / IoT sensors."""

    __tablename__ = "meteo_observations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    station_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    station_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # PostGIS Point Location (Longitude, Latitude)
    location_geom: Mapped[Optional[Any]] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    observation_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    air_temp_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    relative_humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    solar_radiation_wm2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_speed_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    surface_pressure_hpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    __table_args__ = (
        Index("ix_meteo_station_time", "station_id", "observation_time"),
    )
