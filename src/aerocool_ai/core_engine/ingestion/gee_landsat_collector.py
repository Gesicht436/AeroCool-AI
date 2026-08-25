"""Landsat 8/9 Land Surface Temperature (LST) Ingestion via Google Earth Engine (GEE).

Collects Collection 2 Level-2 Surface Temperature (ST_B10) with radiometric calibration,
QA_PIXEL cloud and shadow masking, and spatial cropping.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from aerocool_ai.config import Settings, get_settings

logger = logging.getLogger(__name__)

_GLOBAL_EE_INITIALIZED: Optional[bool] = None


@dataclass
class LSTRasterResult:
    """Container for processed Land Surface Temperature raster observations."""

    data: np.ndarray  # Shape (H, W), values in Celsius
    transform: Tuple[float, float, float, float, float, float]  # Affine transform parameters
    crs: str  # e.g. "EPSG:4326" or "EPSG:32633"
    bounds: Tuple[float, float, float, float]  # (minx, miny, maxx, maxy)
    timestamp: str
    sensor: str
    cloud_cover_percentage: float
    metadata: Dict[str, Any]


class LandsatLSTCollector:
    """Earth Engine client for Landsat 8 and 9 Thermal Infrared Sensor (TIRS) data."""

    # Landsat Collection 2 Level-2 ST_B10 Scaling Constants
    SCALE_FACTOR: float = 0.00341802
    OFFSET: float = 149.0
    KELVIN_TO_CELSIUS: float = -273.15

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._ee_initialized = self._initialize_ee()

    def _initialize_ee(self) -> bool:
        """Authenticate and initialize the Earth Engine client."""
        global _GLOBAL_EE_INITIALIZED
        if _GLOBAL_EE_INITIALIZED is not None:
            return _GLOBAL_EE_INITIALIZED

        try:
            import ee

            if self.settings.gee_service_account and self.settings.gee_private_key_file:
                credentials = ee.ServiceAccountCredentials(
                    self.settings.gee_service_account,
                    self.settings.gee_private_key_file,
                )
                ee.Initialize(credentials=credentials)
                _GLOBAL_EE_INITIALIZED = True
                logger.info("Google Earth Engine initialized via Service Account.")
            elif self.settings.gee_project_id:
                ee.Initialize(project=self.settings.gee_project_id)
                _GLOBAL_EE_INITIALIZED = True
                logger.info(f"Google Earth Engine initialized for project {self.settings.gee_project_id}.")
            else:
                try:
                    ee.Initialize()
                    _GLOBAL_EE_INITIALIZED = True
                    logger.info("Google Earth Engine initialized using existing session tokens.")
                except Exception as e:
                    logger.warning(f"Default GEE initialization deferred: {e}")
                    _GLOBAL_EE_INITIALIZED = False
        except ImportError:
            logger.error("Earth Engine API (earthengine-api) is not installed.")
            _GLOBAL_EE_INITIALIZED = False
        except Exception as exc:
            logger.error(f"GEE initialization failed: {exc}.")
            _GLOBAL_EE_INITIALIZED = False

        return _GLOBAL_EE_INITIALIZED

    def is_available(self) -> bool:
        """Check if Earth Engine authentication is active."""
        return self._ee_initialized

    @classmethod
    def apply_thermal_scaling(cls, digital_numbers: np.ndarray) -> np.ndarray:
        """Convert raw Landsat C2 L2 ST_B10 DN to degrees Celsius.

        Formula:
            T (Kelvin) = DN * 0.00341802 + 149.0
            T (Celsius) = T (Kelvin) - 273.15
        """
        kelvin = digital_numbers * cls.SCALE_FACTOR + cls.OFFSET
        celsius = kelvin + cls.KELVIN_TO_CELSIUS
        # Filter unphysical values (e.g. fill values)
        celsius[digital_numbers == 0] = np.nan
        return celsius

    @classmethod
    def decode_qa_cloud_mask(cls, qa_pixel: np.ndarray) -> np.ndarray:
        """Decode Landsat QA_PIXEL bitmask to identify clear pixels."""
        # Bits 1 (dilated cloud), 3 (cloud), 4 (shadow)
        mask = (qa_pixel & (1 << 1)) | (qa_pixel & (1 << 3)) | (qa_pixel & (1 << 4))
        return mask == 0  # True means clear sky

    def fetch_lst_aoi(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        max_cloud_cover: float = 20.0,
        resolution_meters: int = 30,
    ) -> LSTRasterResult:
        """Fetch Landsat 8/9 LST composite for a given Bounding Box [min_lon, min_lat, max_lon, max_lat]."""
        min_lon, min_lat, max_lon, max_lat = bbox

        if not self._ee_initialized:
            raise RuntimeError(
                "Google Earth Engine is not authenticated. Please run 'earthengine authenticate' "
                "in your terminal or configure GEE_SERVICE_ACCOUNT / GEE_PROJECT_ID in your .env file."
            )

        try:
            import ee

            roi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

            def mask_landsat_sr(image: ee.Image) -> ee.Image:
                qa = image.select("QA_PIXEL")
                cloud_shadow_mask = qa.bitwiseAnd(1 << 4).eq(0)
                clouds_mask = qa.bitwiseAnd(1 << 3).eq(0)
                dilated_cloud_mask = qa.bitwiseAnd(1 << 1).eq(0)
                mask = cloud_shadow_mask.And(clouds_mask).And(dilated_cloud_mask)
                return image.updateMask(mask)

            l8 = (
                ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                .filterBounds(roi)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUD_COVER", max_cloud_cover))
                .map(mask_landsat_sr)
            )

            l9 = (
                ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                .filterBounds(roi)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUD_COVER", max_cloud_cover))
                .map(mask_landsat_sr)
            )

            merged = l8.merge(l9)
            count = merged.size().getInfo()

            if count == 0:
                raise RuntimeError(
                    f"No cloud-free Landsat scenes found for bounding box {bbox} between {start_date} and {end_date}."
                )

            composite = merged.median()
            st_b10 = composite.select("ST_B10")
            # Apply scaling: K -> C
            lst_celsius = st_b10.multiply(self.SCALE_FACTOR).add(self.OFFSET).add(self.KELVIN_TO_CELSIUS)

            # Sample region
            pixel_array = lst_celsius.sampleRectangle(region=roi, defaultValue=np.nan).getInfo()
            data = np.array(pixel_array["properties"]["ST_B10"], dtype=np.float32)

            h, w = data.shape
            dx = (max_lon - min_lon) / max(w, 1)
            dy = -(max_lat - min_lat) / max(h, 1)
            transform = (min_lon, dx, 0.0, max_lat, 0.0, dy)

            return LSTRasterResult(
                data=data,
                transform=transform,
                crs="EPSG:4326",
                bounds=bbox,
                timestamp=f"{start_date}/{end_date}",
                sensor="Landsat-8/9-TIRS",
                cloud_cover_percentage=float(max_cloud_cover),
                metadata={"scene_count": count, "resolution_m": resolution_meters},
            )

        except Exception as exc:
            logger.error(f"Error querying Landsat GEE: {exc}")
            raise RuntimeError(f"Google Earth Engine Landsat query failed: {exc}") from exc
