"""Spatial Raster and Vector Layer Catalog Models.

Represents geospatial metadata, bounding geometries, and raster/vector layer records in PostGIS.
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


class SpatialRasterLayer(Base):
    """Catalog table for geospatial raster assets (LST, NDVI, Albedo, LULC, SVF)."""

    __tablename__ = "spatial_raster_layers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    layer_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    layer_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g., "LST", "NDVI", "ALBEDO", "LULC", "SVF"
    sensor_source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., "Landsat-8", "Sentinel-2", "ECOSTRESS"
    resolution_meters: Mapped[float] = mapped_column(Float, default=30.0)
    crs: Mapped[str] = mapped_column(String(20), default="EPSG:4326")

    # PostGIS Spatial Bounding Polygon
    bounds_geom: Mapped[Optional[Any]] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )

    storage_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    layer_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    __table_args__ = (
        Index("ix_raster_layer_type_time", "layer_type", "timestamp"),
    )


class SpatialVectorFeature(Base):
    """Vector features: building footprints, land parcels, parks, street canyons."""

    __tablename__ = "spatial_vector_features"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    feature_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # "building", "parcel", "green_space", "road"
    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=False,
    )
    height_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    plan_area_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    albedo: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fvc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    properties: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
