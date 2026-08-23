"""Spatial Layer Catalog Repository.

Provides async CRUD and PostGIS spatial queries (ST_Intersects, ST_Within, ST_MakeEnvelope)
for raster catalogs and vector geometries.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from geoalchemy2.functions import ST_GeomFromText, ST_Intersects, ST_MakeEnvelope
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aerocool_ai.database.models.spatial_layers import (
    SpatialRasterLayer,
    SpatialVectorFeature,
)

logger = logging.getLogger(__name__)


class LayerRepository:
    """Async repository for querying spatial layers and geospatial vector geometries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_raster_layer(
        self,
        layer_name: str,
        layer_type: str,
        sensor_source: str,
        storage_uri: str,
        timestamp: datetime.datetime,
        bounds_bbox: Optional[Tuple[float, float, float, float]] = None,
        resolution_meters: float = 30.0,
        crs: str = "EPSG:4326",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SpatialRasterLayer:
        """Insert a new spatial raster catalog entry."""
        geom = None
        if bounds_bbox:
            minx, miny, maxx, maxy = bounds_bbox
            geom = ST_MakeEnvelope(minx, miny, maxx, maxy, 4326)

        layer = SpatialRasterLayer(
            layer_name=layer_name,
            layer_type=layer_type.upper(),
            sensor_source=sensor_source,
            storage_uri=storage_uri,
            timestamp=timestamp,
            bounds_geom=geom,
            resolution_meters=resolution_meters,
            crs=crs,
            layer_metadata=metadata or {},
        )
        self.session.add(layer)
        await self.session.flush()
        return layer

    async def get_raster_layer_by_id(self, layer_id: str) -> Optional[SpatialRasterLayer]:
        """Fetch a raster layer by UUID."""
        stmt = select(SpatialRasterLayer).where(SpatialRasterLayer.id == layer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_raster_layers(
        self,
        layer_type: Optional[str] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SpatialRasterLayer]:
        """List raster layers with optional spatial bounding box and type filters."""
        stmt = select(SpatialRasterLayer).order_by(desc(SpatialRasterLayer.timestamp))

        if layer_type:
            stmt = stmt.where(SpatialRasterLayer.layer_type == layer_type.upper())

        if bbox:
            minx, miny, maxx, maxy = bbox
            envelope = ST_MakeEnvelope(minx, miny, maxx, maxy, 4326)
            stmt = stmt.where(ST_Intersects(SpatialRasterLayer.bounds_geom, envelope))

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_vector_feature(
        self,
        feature_type: str,
        wkt_geometry: str,
        height_m: Optional[float] = None,
        plan_area_m2: Optional[float] = None,
        albedo: Optional[float] = None,
        fvc: Optional[float] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> SpatialVectorFeature:
        """Insert a vector geometry feature."""
        geom = ST_GeomFromText(wkt_geometry, 4326)
        feature = SpatialVectorFeature(
            feature_type=feature_type,
            geometry=geom,
            height_m=height_m,
            plan_area_m2=plan_area_m2,
            albedo=albedo,
            fvc=fvc,
            properties=properties or {},
        )
        self.session.add(feature)
        await self.session.flush()
        return feature

    async def query_vector_features_in_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        feature_type: Optional[str] = None,
        limit: int = 1000,
    ) -> List[SpatialVectorFeature]:
        """Spatial query returning vector features intersecting bounding box."""
        minx, miny, maxx, maxy = bbox
        envelope = ST_MakeEnvelope(minx, miny, maxx, maxy, 4326)

        stmt = select(SpatialVectorFeature).where(
            ST_Intersects(SpatialVectorFeature.geometry, envelope)
        )

        if feature_type:
            stmt = stmt.where(SpatialVectorFeature.feature_type == feature_type)

        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
