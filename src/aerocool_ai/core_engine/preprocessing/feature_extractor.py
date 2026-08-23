"""Biophysical Indices and Morphometric Feature Extractor.

Calculates key thermodynamic and spectral indicators for urban microclimate modeling:
- Normalized Difference Vegetation Index (NDVI)
- Normalized Difference Built-Up Index (NDBI)
- Normalized Difference Water Index (NDWI)
- Broadband Shortwave Surface Albedo (alpha) via Liang (2001) multispectral formula
- Fractional Vegetation Cover (FVC / f_v)
- Land Surface Thermal Emissivity (epsilon)
- Sky View Factor (SVF) from 3D building morphology
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np
from scipy.ndimage import uniform_filter

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFeatureSet:
    """Consolidated thermodynamic and biophysical feature cube."""

    ndvi: np.ndarray  # Normalized Difference Vegetation Index [-1, 1]
    ndbi: np.ndarray  # Normalized Difference Built-Up Index [-1, 1]
    ndwi: np.ndarray  # Normalized Difference Water Index [-1, 1]
    albedo: np.ndarray  # Broadband surface albedo [0, 1]
    fvc: np.ndarray  # Fractional Vegetation Cover [0, 1]
    emissivity: np.ndarray  # Surface thermal emissivity [0.85, 0.99]
    sky_view_factor: np.ndarray  # Sky View Factor (SVF) [0, 1]
    impervious_fraction: np.ndarray  # Impervious surface fraction [0, 1]
    metadata: Dict[str, Any]


class UrbanFeatureExtractor:
    """Extracts urban biophysical and microclimatic parameters from optical and morphology data."""

    # Sobrino et al. (2004) Emissivity Constants
    EMISSIVITY_VEGETATION: float = 0.985
    EMISSIVITY_SOIL: float = 0.960
    EMISSIVITY_WATER: float = 0.990
    EMISSIVITY_BUILT: float = 0.930

    NDVI_SOIL: float = 0.05
    NDVI_VEG: float = 0.70

    @classmethod
    def calculate_ndvi(cls, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Compute Normalized Difference Vegetation Index (NDVI = (NIR - Red) / (NIR + Red))."""
        denom = nir + red
        denom = np.where(denom == 0, 1e-6, denom)
        ndvi = (nir - red) / denom
        return np.clip(ndvi, -1.0, 1.0).astype(np.float32)

    @classmethod
    def calculate_ndbi(cls, swir: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Compute Normalized Difference Built-Up Index (NDBI = (SWIR - NIR) / (SWIR + NIR))."""
        denom = swir + nir
        denom = np.where(denom == 0, 1e-6, denom)
        ndbi = (swir - nir) / denom
        return np.clip(ndbi, -1.0, 1.0).astype(np.float32)

    @classmethod
    def calculate_ndwi(cls, green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Compute Normalized Difference Water Index (NDWI = (Green - NIR) / (Green + NIR))."""
        denom = green + nir
        denom = np.where(denom == 0, 1e-6, denom)
        ndwi = (green - nir) / denom
        return np.clip(ndwi, -1.0, 1.0).astype(np.float32)

    @classmethod
    def calculate_broadband_albedo(
        cls,
        blue: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir1: np.ndarray,
        swir2: np.ndarray,
    ) -> np.ndarray:
        """Compute broadband surface albedo via Liang (2001) multispectral transformation.

        alpha = 0.356 * B2 + 0.130 * B4 + 0.373 * B8 + 0.085 * B11 + 0.072 * B12 - 0.0018
        """
        albedo = (
            0.356 * blue
            + 0.130 * red
            + 0.373 * nir
            + 0.085 * swir1
            + 0.072 * swir2
            - 0.0018
        )
        return np.clip(albedo, 0.02, 0.85).astype(np.float32)

    @classmethod
    def calculate_fvc(cls, ndvi: np.ndarray) -> np.ndarray:
        """Compute Fractional Vegetation Cover (FVC) using NDVI threshold method.

        FVC = ((NDVI - NDVI_soil) / (NDVI_veg - NDVI_soil))^2
        """
        fvc = ((ndvi - cls.NDVI_SOIL) / max(cls.NDVI_VEG - cls.NDVI_SOIL, 1e-4)) ** 2
        fvc = np.where(ndvi < cls.NDVI_SOIL, 0.0, fvc)
        fvc = np.where(ndvi > cls.NDVI_VEG, 1.0, fvc)
        return np.clip(fvc, 0.0, 1.0).astype(np.float32)

    @classmethod
    def calculate_surface_emissivity(
        cls,
        ndvi: np.ndarray,
        fvc: np.ndarray,
        ndwi: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Estimate surface thermal emissivity (epsilon) using NDVI threshold method (Sobrino et al.).

        - Water: epsilon = 0.990
        - Bare Soil (NDVI < NDVI_soil): epsilon = 0.960
        - Full Vegetation (NDVI > NDVI_veg): epsilon = 0.985
        - Mixed Urban/Vegetation: epsilon = epsilon_v * FVC + epsilon_s * (1 - FVC) + d_epsilon
        """
        # Cavity effect term d_epsilon = 4 * <sigma> * FVC * (1 - FVC)
        d_epsilon = 0.004 * fvc * (1.0 - fvc)
        emissivity = (
            cls.EMISSIVITY_VEGETATION * fvc
            + cls.EMISSIVITY_SOIL * (1.0 - fvc)
            + d_epsilon
        )

        if ndwi is not None:
            water_mask = ndwi > 0.15
            emissivity = np.where(water_mask, cls.EMISSIVITY_WATER, emissivity)

        return np.clip(emissivity, 0.88, 0.995).astype(np.float32)

    @classmethod
    def estimate_sky_view_factor(
        cls,
        building_height: np.ndarray,
        plan_area_fraction: np.ndarray,
        street_width_m: float = 16.0,
    ) -> np.ndarray:
        """Estimate Sky View Factor (SVF) from building heights and building density.

        Approximation using Oke's street canyon model:
            Aspect ratio H/W = building_height / street_width
            SVF = cos(arctan(2 * H / W))
        """
        h_eff = building_height * np.sqrt(np.clip(plan_area_fraction, 0.05, 1.0))
        aspect_ratio = (2.0 * h_eff) / max(street_width_m, 1.0)
        svf = np.cos(np.arctan(aspect_ratio))
        # Open parks and water have SVF ~ 1.0
        svf = np.where(plan_area_fraction < 0.05, 0.98, svf)
        return np.clip(svf, 0.15, 1.0).astype(np.float32)

    def extract_features(
        self,
        blue: np.ndarray,
        green: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir1: np.ndarray,
        swir2: np.ndarray,
        building_height: np.ndarray,
        plan_area_fraction: np.ndarray,
    ) -> ExtractedFeatureSet:
        """Compute all biophysical and morphometric features in a unified pipeline."""
        ndvi = self.calculate_ndvi(red, nir)
        ndbi = self.calculate_ndbi(swir1, nir)
        ndwi = self.calculate_ndwi(green, nir)
        albedo = self.calculate_broadband_albedo(blue, red, nir, swir1, swir2)
        fvc = self.calculate_fvc(ndvi)
        emissivity = self.calculate_surface_emissivity(ndvi, fvc, ndwi)
        svf = self.estimate_sky_view_factor(building_height, plan_area_fraction)

        # Impervious surface fraction
        impervious = np.clip(0.6 * np.maximum(0, ndbi) + 0.4 * plan_area_fraction - 0.3 * fvc, 0.0, 1.0)

        return ExtractedFeatureSet(
            ndvi=ndvi,
            ndbi=ndbi,
            ndwi=ndwi,
            albedo=albedo,
            fvc=fvc,
            emissivity=emissivity,
            sky_view_factor=svf,
            impervious_fraction=impervious.astype(np.float32),
            metadata={"extracted_features": 8, "grid_shape": list(ndvi.shape)},
        )
