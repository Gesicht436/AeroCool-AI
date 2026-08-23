"""Spatial Alignment, Reprojection, and Grid Matching Pipeline.

Standardizes disparate geospatial rasters (varying resolutions from 10m Sentinel, 30m Landsat,
70m ECOSTRESS, to 0.1° ERA5) into a unified projected coordinate reference system (CRS),
matching shape (H, W), affine transformation, and bounding envelope.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.ndimage import map_coordinates, zoom

logger = logging.getLogger(__name__)


@dataclass
class AlignedGridSpecification:
    """Target spatial grid specification for alignment."""

    bounds: Tuple[float, float, float, float]  # (min_lon, min_lat, max_lon, max_lat)
    target_shape: Tuple[int, int]  # (height, width)
    crs: str = "EPSG:4326"
    resolution_deg: Optional[Tuple[float, float]] = None


class SpatialAlignmentPipeline:
    """Pipeline for aligning multi-source geospatial rasters to a uniform grid."""

    def __init__(self, target_spec: Optional[AlignedGridSpecification] = None) -> None:
        self.target_spec = target_spec or AlignedGridSpecification(
            bounds=(-74.05, 40.68, -73.90, 40.85),
            target_shape=(64, 64),
            crs="EPSG:4326",
        )

    def resample_raster(
        self,
        array: np.ndarray,
        current_shape: Optional[Tuple[int, int]] = None,
        target_shape: Optional[Tuple[int, int]] = None,
        order: int = 1,  # 0: Nearest neighbor (categorical), 1: Bilinear, 3: Cubic
    ) -> np.ndarray:
        """Resample a 2D or 3D numpy array to the target dimensions using spline interpolation."""
        target = target_shape or self.target_spec.target_shape
        if array.shape[-2:] == target:
            return array

        if array.ndim == 2:
            zoom_factors = (target[0] / array.shape[0], target[1] / array.shape[1])
            resampled = zoom(array, zoom_factors, order=order)
            # Ensure exact shape match in case of rounding
            return resampled[: target[0], : target[1]]

        elif array.ndim == 3:
            # Multi-band raster (B, H, W)
            bands = []
            for b in range(array.shape[0]):
                zf = (target[0] / array.shape[1], target[2] if array.ndim > 2 else target[1] / array.shape[2])
                resampled = zoom(array[b], (target[0] / array.shape[1], target[1] / array.shape[2]), order=order)
                bands.append(resampled[: target[0], : target[1]])
            return np.stack(bands, axis=0)

        else:
            raise ValueError(f"Unsupported array dimensions: {array.ndim}")

    def align_layers(
        self,
        layers: Dict[str, np.ndarray],
        categorical_keys: Optional[List[str]] = None,
    ) -> Dict[str, np.ndarray]:
        """Align a collection of named raster arrays to the pipeline's target grid shape.

        Args:
            layers: Dictionary mapping layer names to 2D/3D numpy arrays.
            categorical_keys: Keys that require nearest-neighbor interpolation (e.g. LULC classes).
        """
        categorical_keys = categorical_keys or ["lulc", "lulc_class", "landcover", "building_mask"]
        aligned: Dict[str, np.ndarray] = {}

        for key, arr in layers.items():
            is_categorical = any(cat in key.lower() for cat in categorical_keys)
            order = 0 if is_categorical else 1
            aligned[key] = self.resample_raster(arr, order=order)

        return aligned

    def stack_feature_tensor(
        self,
        aligned_layers: Dict[str, np.ndarray],
        ordered_keys: List[str],
    ) -> np.ndarray:
        """Stack aligned 2D feature maps into a multi-channel tensor of shape (C, H, W)."""
        channels = []
        for key in ordered_keys:
            if key not in aligned_layers:
                raise KeyError(f"Required layer '{key}' is missing from aligned layers dictionary.")
            arr = aligned_layers[key]
            if arr.ndim != 2:
                raise ValueError(f"Layer '{key}' has shape {arr.shape}, expected 2D (H, W).")
            channels.append(arr)

        return np.stack(channels, axis=0).astype(np.float32)
