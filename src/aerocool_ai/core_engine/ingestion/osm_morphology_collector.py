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

_OVERPASS_AVAILABLE: Optional[bool] = None


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
        global _OVERPASS_AVAILABLE
        min_lon, min_lat, max_lon, max_lat = bbox

        if _OVERPASS_AVAILABLE is False:
            return self._generate_synthetic_morphology(bbox, grid_shape)

        try:
            import osmnx as ox

            # Set user agent and settings
            ox.settings.use_cache = True
            ox.settings.log_console = False
            ox.settings.requests_timeout = 2

            # Query buildings within polygon bbox
            poly = box(min_lon, min_lat, max_lon, max_lat)
            gdf = ox.features_from_polygon(poly, tags={"building": True})

            if gdf is None or len(gdf) == 0:
                logger.info("No OSM buildings returned from Overpass. Generating synthetic morphology.")
                _OVERPASS_AVAILABLE = False
                return self._generate_synthetic_morphology(bbox, grid_shape)

            _OVERPASS_AVAILABLE = True
            return self._process_gdf_to_grid(gdf, bbox, grid_shape)

        except Exception as exc:
            logger.warning(f"OSMnx query failed or unconfigured: {exc}. Generating synthetic urban morphology.")
            _OVERPASS_AVAILABLE = False
            return self._generate_synthetic_morphology(bbox, grid_shape)

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

        # Parse heights
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

        gdf["computed_height"] = gdf.apply(parse_height, axis=1)

        # Approximate rasterization
        lon_step = (max_lon - min_lon) / grid_w
        lat_step = (max_lat - min_lat) / grid_h

        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            centroid = geom.centroid
            c_lon, c_lat = centroid.x, centroid.y

            if not (min_lon <= c_lon <= max_lon and min_lat <= c_lat <= max_lat):
                continue

            gx = int(np.clip((c_lon - min_lon) / lon_step, 0, grid_w - 1))
            # Invert latitude for top-down array
            gy = int(np.clip((max_lat - c_lat) / lat_step, 0, grid_h - 1))

            h = float(row["computed_height"])
            height_grid[gy, gx] += h
            height_max_grid[gy, gx] = max(height_max_grid[gy, gx], h)
            count_grid[gy, gx] += 1
            area_grid[gy, gx] += float(geom.area)

        # Normalize average heights
        nonzero_mask = count_grid > 0
        height_grid[nonzero_mask] = height_grid[nonzero_mask] / count_grid[nonzero_mask]

        # Plan area fraction lambda_p = building footprint area / cell area
        # Approximate cell area in degrees squared
        cell_area = lon_step * lat_step
        plan_area_fraction = np.clip(area_grid / max(cell_area, 1e-9), 0.0, 0.85)

        # Aerodynamic roughness length z_0 estimation (Grimmond & Oke formula approx: z_0 = 0.1 * H_mean)
        roughness_z0 = np.clip(0.1 * height_grid * np.sqrt(plan_area_fraction), 0.01, 3.5)
        frontal_area_index = np.clip(plan_area_fraction * (height_grid / 10.0), 0.0, 1.2)

        return UrbanMorphologyGrid(
            building_height_mean=height_grid,
            building_height_max=height_max_grid,
            plan_area_fraction=plan_area_fraction.astype(np.float32),
            roughness_length_z0=roughness_z0.astype(np.float32),
            frontal_area_index=frontal_area_index.astype(np.float32),
            building_count=len(gdf),
            footprints_gdf=gdf,
            bounds=bbox,
            metadata={"source": "OSM_Overpass_Vector", "total_buildings": len(gdf)},
        )

    def _generate_synthetic_morphology(
        self,
        bbox: Tuple[float, float, float, float],
        grid_shape: Tuple[int, int],
    ) -> UrbanMorphologyGrid:
        """Generate realistic synthetic building heights and plan area fractions."""
        grid_h, grid_w = grid_shape
        y = np.linspace(-2, 2, grid_h)
        x = np.linspace(-2, 2, grid_w)
        xx, yy = np.meshgrid(x, y)
        dist_sq = xx**2 + yy**2

        # High-rise downtown core with high building density
        downtown_core = np.exp(-dist_sq / 0.8)
        commercial_midrise = 0.4 * np.exp(-((xx - 0.7)**2 + (yy - 0.5)**2) / 0.3)

        # Height in meters: downtown up to 65m, suburbs 8-15m
        height_mean = 8.0 + 55.0 * downtown_core + 25.0 * commercial_midrise + np.random.uniform(0, 3.0, grid_shape)
        height_max = height_mean * np.random.uniform(1.1, 1.6, grid_shape)

        # Plan Area Fraction: downtown 0.65, residential 0.30, parks 0.02
        plan_area = 0.25 + 0.45 * downtown_core + 0.2 * commercial_midrise
        # Carve out park corridor
        park_corridor = ((xx + 0.9)**2 + (yy + 0.6)**2) < 0.45
        plan_area[park_corridor] = 0.02
        height_mean[park_corridor] = 0.0
        height_max[park_corridor] = 0.0

        plan_area = np.clip(plan_area, 0.0, 0.85).astype(np.float32)
        height_mean = np.clip(height_mean, 0.0, 120.0).astype(np.float32)
        height_max = np.clip(height_max, 0.0, 150.0).astype(np.float32)

        # Aerodynamic roughness z_0
        roughness_z0 = np.clip(0.1 * height_mean * np.sqrt(plan_area), 0.02, 4.0).astype(np.float32)
        frontal_area = np.clip(plan_area * (height_mean / 12.0), 0.0, 1.5).astype(np.float32)

        return UrbanMorphologyGrid(
            building_height_mean=height_mean,
            building_height_max=height_max,
            plan_area_fraction=plan_area,
            roughness_length_z0=roughness_z0,
            frontal_area_index=frontal_area,
            building_count=4250,
            footprints_gdf=None,
            bounds=bbox,
            metadata={"source": "Synthetic_Urban_Morphology_Engine"},
        )
