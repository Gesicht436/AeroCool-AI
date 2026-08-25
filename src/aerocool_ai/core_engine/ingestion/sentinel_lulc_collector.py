"""Sentinel-2 Multispectral Surface Reflectance & LULC Classification Collector.

Extracts optical bands (Blue, Green, Red, NIR, SWIR-1, SWIR-2) and categorical Land Use /
Land Cover (LULC) data (ESA WorldCover / Dynamic World 10m classes).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, Optional, Tuple

import numpy as np

from aerocool_ai.config import Settings, get_settings

logger = logging.getLogger(__name__)


class LULCClass(IntEnum):
    """Standardized 10m Land Use / Land Cover Classes."""

    WATER = 10
    TREES = 20
    SHRUBLAND = 30
    GRASSLAND = 40
    CROPLAND = 50
    BUILT_UP_HIGH_DENSITY = 60
    BUILT_UP_RESIDENTIAL = 61
    BARE_SOIL = 70
    SNOW_ICE = 80
    ROADS_IMPERVIOUS = 90


@dataclass
class SentinelLULCResult:
    """Multispectral optical reflectance and LULC categorical classification container."""

    blue: np.ndarray  # Band 2 (490 nm)
    green: np.ndarray  # Band 3 (560 nm)
    red: np.ndarray  # Band 4 (665 nm)
    nir: np.ndarray  # Band 8 (842 nm)
    swir1: np.ndarray  # Band 11 (1610 nm)
    swir2: np.ndarray  # Band 12 (2190 nm)
    lulc_class: np.ndarray  # Categorical integer array
    cloud_mask: np.ndarray  # Boolean mask (True = clear, False = cloudy)
    transform: Tuple[float, float, float, float, float, float]
    crs: str
    bounds: Tuple[float, float, float, float]
    resolution_m: float
    timestamp: str
    metadata: Dict[str, Any]


class SentinelLULCCollector:
    """Ingestion collector for Sentinel-2 Level-2A surface reflectance and LULC products."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def fetch_multispectral_and_lulc(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        cloud_threshold: float = 15.0,
    ) -> SentinelLULCResult:
        """Fetch Sentinel-2 multispectral surface reflectance and LULC maps for an AOI."""
        min_lon, min_lat, max_lon, max_lat = bbox

        try:
            import ee
            ee.Initialize()
            roi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

            # Query Sentinel-2 Harmonized
            s2 = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(roi)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
                .median()
                .divide(10000.0)
            )

            # Sample bands
            bands_data = s2.select(["B2", "B3", "B4", "B8", "B11", "B12"]).sampleRectangle(region=roi).getInfo()
            props = bands_data["properties"]
            blue = np.array(props["B2"], dtype=np.float32)
            green = np.array(props["B3"], dtype=np.float32)
            red = np.array(props["B4"], dtype=np.float32)
            nir = np.array(props["B8"], dtype=np.float32)
            swir1 = np.array(props["B11"], dtype=np.float32)
            swir2 = np.array(props["B12"], dtype=np.float32)

            grid_h, grid_w = blue.shape

            # Query ESA WorldCover
            wc = ee.ImageCollection("ESA/WorldCover/v100").first().select("Map")
            wc_data = wc.sampleRectangle(region=roi).getInfo()
            lulc_grid = np.array(wc_data["properties"]["Map"], dtype=np.uint8)

            dx = (max_lon - min_lon) / max(grid_w, 1)
            dy = -(max_lat - min_lat) / max(grid_h, 1)
            transform = (min_lon, dx, 0.0, max_lat, 0.0, dy)

            return SentinelLULCResult(
                blue=blue,
                green=green,
                red=red,
                nir=nir,
                swir1=swir1,
                swir2=swir2,
                lulc_class=lulc_grid,
                cloud_mask=np.ones((grid_h, grid_w), dtype=bool),
                transform=transform,
                crs="EPSG:4326",
                bounds=bbox,
                resolution_m=10.0,
                timestamp=f"{start_date}/{end_date}",
                metadata={"source": "Sentinel-2A/B-MSI-L2A", "grid_shape": [grid_h, grid_w]},
            )

        except Exception as exc:
            raise RuntimeError(
                f"Sentinel-2 & LULC data provider query failed: {exc}. "
                "Ensure Google Earth Engine is authenticated via 'earthengine authenticate' or configure GEE credentials in .env."
            ) from exc
