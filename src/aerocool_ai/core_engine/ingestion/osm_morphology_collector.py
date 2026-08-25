"""OpenStreetMap (OSM) Urban Morphology & Building Geometry Collector.

Queries vector geometries for buildings, street networks, and calculates
key 3D urban canopy parameters:
- Plan Area Fraction (lambda_p): Building footprint density
- Mean Building Height (H_mean) and Roughness Length (z_0)
- Frontal Area Index (lambda_f)
- Canyon Aspect Ratio (Height / Width)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, box

from aerocool_ai.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class UrbanMorphologyGrid:
    """Rasterized urban morphology parameters on a regular grid."""

    building_height_mean: np.ndarray  # (H, W) in meters
    building_height_max: np.ndarray  # (H, W) in meters
    plan_area_fraction: np.ndarray  # lambda_p in [0.0, 1.0]
    roughness_length_z0: np.ndarray  # Aerodynamic roughness length in meters
    frontal_area_index: np.ndarray  # lambda_f
    building_count: int
    footprints_gdf: Optional[gpd.GeoDataFrame]
    bounds: Tuple[float, float, float, float]
    metadata: Dict[str, Any]


class OSMMorphologyCollector:
    """Urban morphology collector utilizing OSMnx and Overpass vector geometries."""

    DEFAULT_STOREY_HEIGHT_M: float = 3.2  # Average meters per building level
    DEFAULT_BUILDING_HEIGHT_M: float = 8.5  # Fallback 2-3 storey residential height

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def fetch_morphology(
        self,
        bbox: Tuple[float, float, float, float],
        grid_shape: Tuple[int, int] = (64, 64),
    ) -> UrbanMorphologyGrid:
        """Query building footprints within bbox and compute rasterized morphology metrics."""
        min_lon, min_lat, max_lon, max_lat = bbox

        try:
            import osmnx as ox

            ox.settings.use_cache = True
            ox.settings.log_console = False
            ox.settings.requests_timeout = 10

            poly = box(min_lon, min_lat, max_lon, max_lat)
            gdf = ox.features_from_polygon(poly, tags={"building": True})

            if gdf is None or len(gdf) == 0:
                raise RuntimeError(f"No OpenStreetMap building footprints found for bounding box {bbox}.")

            return self._process_gdf_to_grid(gdf, bbox, grid_shape)

        except Exception as exc:
            logger.error(f"OSMnx Overpass query failed: {exc}")
            raise RuntimeError(
                f"OpenStreetMap Overpass API building query failed ({exc}). "
                "Ensure internet connectivity and that the bounding box covers an urban area with mapped footprints."
            ) from exc

    def _process_gdf_to_grid(
        self,
        gdf: gpd.GeoDataFrame,
        bbox: Tuple[float, float, float, float],
        grid_shape: Tuple[int, int],
    ) -> UrbanMorphologyGrid:
        """Rasterize building vectors into continuous morphometric grids."""
        min_lon, min_lat, max_lon, max_lat = bbox
        grid_h, grid_w = grid_shape

        height_grid = np.zeros(grid_shape, dtype=np.float32)
        height_max_grid = np.zeros(grid_shape, dtype=np.float32)
        count_grid = np.zeros(grid_shape, dtype=np.float32)
        area_grid = np.zeros(grid_shape, dtype=np.float32)

        def parse_height(row: Any) -> float:
            if "height" in row and row["height"] is not None and not (isinstance(row["height"], float) and np.isnan(row["height"])):
                try:
                    return float(str(row["height"]).replace("m", "").strip())
                except (ValueError, TypeError):
                    pass
            if "building:levels" in row and row["building:levels"] is not None and not (isinstance(row["building:levels"], float) and np.isnan(row["building:levels"])):
                try:
                    return float(row["building:levels"]) * self.DEFAULT_STOREY_HEIGHT_M
                except (ValueError, TypeError):
                    pass
            return self.DEFAULT_BUILDING_HEIGHT_M

        if "geometry" in gdf.columns:
            gdf["calc_height"] = gdf.apply(parse_height, axis=1)

            lon_step = (max_lon - min_lon) / grid_w
            lat_step = (max_lat - min_lat) / grid_h
            cell_area_approx = (lon_step * 111320.0) * (lat_step * 110540.0)

            for _, row in gdf.iterrows():
                geom = row.geometry
                if geom is None or geom.is_empty:
                    continue

                c_lon, c_lat = geom.centroid.x, geom.centroid.y
                if not (min_lon <= c_lon <= max_lon and min_lat <= c_lat <= max_lat):
                    continue

                gx = int((c_lon - min_lon) / (max_lon - min_lon) * (grid_w - 1))
                gy = int((max_lat - c_lat) / (max_lat - min_lat) * (grid_h - 1))
                gx = max(0, min(grid_w - 1, gx))
                gy = max(0, min(grid_h - 1, gy))

                h_val = float(row.get("calc_height", self.DEFAULT_BUILDING_HEIGHT_M))
                height_grid[gy, gx] += h_val
                height_max_grid[gy, gx] = max(height_max_grid[gy, gx], h_val)
                count_grid[gy, gx] += 1

                geom_area = getattr(geom, "area", 0.0) * 111320.0 * 110540.0
                area_grid[gy, gx] += geom_area

        # Compute mean building height per pixel
        valid_cells = count_grid > 0
        height_grid[valid_cells] = height_grid[valid_cells] / count_grid[valid_cells]
        height_grid[~valid_cells] = 0.0

        # Plan area fraction (lambda_p)
        lon_step = (max_lon - min_lon) / grid_w
        lat_step = (max_lat - min_lat) / grid_h
        cell_area = (lon_step * 111320.0) * (lat_step * 110540.0)
        lambda_p = np.clip(area_grid / max(cell_area, 1.0), 0.0, 0.95)

        # Grimmond & Oke aerodynamic roughness length z_0 = 0.10 * H_mean * sqrt(lambda_p)
        z0 = 0.10 * height_grid * np.sqrt(np.maximum(lambda_p, 0.01))

        # Frontal area index approximation
        lambda_f = np.clip(lambda_p * (height_grid / max(np.mean(height_grid[valid_cells]), 1.0) if np.any(valid_cells) else 1.0) * 0.5, 0.0, 1.0)

        return UrbanMorphologyGrid(
            building_height_mean=height_grid.astype(np.float32),
            building_height_max=height_max_grid.astype(np.float32),
            plan_area_fraction=lambda_p.astype(np.float32),
            roughness_length_z0=z0.astype(np.float32),
            frontal_area_index=lambda_f.astype(np.float32),
            building_count=int(len(gdf)),
            footprints_gdf=gdf,
            bounds=bbox,
            metadata={"building_count": len(gdf), "grid_shape": list(grid_shape)},
        )
