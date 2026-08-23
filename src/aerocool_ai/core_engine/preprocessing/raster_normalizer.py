"""Raster Normalization, Scaling, and NoData Inpainting Pipeline.

Provides robust statistical normalizations (Z-score, Min-Max, Quantile Robust Scaling)
and spatial interpolation routines for satellite imagery with NoData / cloud gaps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple, Union

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

logger = logging.getLogger(__name__)

NormalizationMethod = Literal["minmax", "zscore", "robust", "none"]


@dataclass
class ChannelStatistics:
    """Statistical parameters for feature scaling and inverse reconstruction."""

    mean: float
    std: float
    min_val: float
    max_val: float
    q25: float
    q75: float
    method: NormalizationMethod


class RasterNormalizer:
    """Scales, standardizes, and repairs missing pixel regions across geospatial tensors."""

    def __init__(self, method: NormalizationMethod = "minmax") -> None:
        self.method = method
        self.channel_stats: Dict[int, ChannelStatistics] = {}

    def fit(self, tensor: np.ndarray) -> "RasterNormalizer":
        """Compute normalization statistics from training tensor of shape (C, H, W) or (N, C, H, W)."""
        if tensor.ndim == 3:
            num_channels = tensor.shape[0]
            for c in range(num_channels):
                data_c = tensor[c].flatten()
                valid = data_c[~np.isnan(data_c)]
                if len(valid) == 0:
                    valid = np.array([0.0, 1.0])

                self.channel_stats[c] = ChannelStatistics(
                    mean=float(np.mean(valid)),
                    std=float(max(np.std(valid), 1e-6)),
                    min_val=float(np.min(valid)),
                    max_val=float(np.max(valid)),
                    q25=float(np.percentile(valid, 25)),
                    q75=float(np.percentile(valid, 75)),
                    method=self.method,
                )
        elif tensor.ndim == 4:
            num_channels = tensor.shape[1]
            for c in range(num_channels):
                data_c = tensor[:, c].flatten()
                valid = data_c[~np.isnan(data_c)]
                if len(valid) == 0:
                    valid = np.array([0.0, 1.0])

                self.channel_stats[c] = ChannelStatistics(
                    mean=float(np.mean(valid)),
                    std=float(max(np.std(valid), 1e-6)),
                    min_val=float(np.min(valid)),
                    max_val=float(np.max(valid)),
                    q25=float(np.percentile(valid, 25)),
                    q75=float(np.percentile(valid, 75)),
                    method=self.method,
                )
        return self

    def transform(self, tensor: np.ndarray) -> np.ndarray:
        """Apply fitted normalization to tensor."""
        normed = tensor.copy()
        if tensor.ndim == 2:
            stats = self.channel_stats.get(
                0,
                ChannelStatistics(
                    mean=0.0,
                    std=1.0,
                    min_val=0.0,
                    max_val=1.0,
                    q25=0.0,
                    q75=1.0,
                    method=self.method,
                ),
            )
            return self._normalize_array(tensor, stats)

        num_channels = tensor.shape[0] if tensor.ndim == 3 else tensor.shape[1]
        for c in range(num_channels):
            if c not in self.channel_stats:
                continue
            stats = self.channel_stats[c]
            if tensor.ndim == 3:
                normed[c] = self._normalize_array(tensor[c], stats)
            elif tensor.ndim == 4:
                normed[:, c] = self._normalize_array(tensor[:, c], stats)

        return normed

    def fit_transform(self, tensor: np.ndarray) -> np.ndarray:
        """Fit statistics and transform tensor in a single call."""
        return self.fit(tensor).transform(tensor)

    def inverse_transform(self, tensor: np.ndarray, channel_idx: int = 0) -> np.ndarray:
        """Invert normalization on a predicted array or tensor."""
        if channel_idx not in self.channel_stats:
            return tensor

        stats = self.channel_stats[channel_idx]
        if stats.method == "minmax":
            range_val = max(stats.max_val - stats.min_val, 1e-6)
            return tensor * range_val + stats.min_val
        elif stats.method == "zscore":
            return tensor * stats.std + stats.mean
        elif stats.method == "robust":
            iqr = max(stats.q75 - stats.q25, 1e-6)
            median = (stats.q75 + stats.q25) / 2.0
            return tensor * iqr + median
        return tensor

    def _normalize_array(self, arr: np.ndarray, stats: ChannelStatistics) -> np.ndarray:
        """Normalize array based on statistical parameters."""
        if stats.method == "minmax":
            denom = max(stats.max_val - stats.min_val, 1e-6)
            return np.clip((arr - stats.min_val) / denom, 0.0, 1.0)
        elif stats.method == "zscore":
            return (arr - stats.mean) / stats.std
        elif stats.method == "robust":
            iqr = max(stats.q75 - stats.q25, 1e-6)
            median = (stats.q75 + stats.q25) / 2.0
            return (arr - median) / iqr
        return arr

    @staticmethod
    def inpaint_nodata(
        raster: np.ndarray,
        nodata_mask: Optional[np.ndarray] = None,
        method: Literal["nearest", "gaussian"] = "nearest",
    ) -> np.ndarray:
        """Inpaint missing pixels / NoData / Cloud gaps using spatial interpolation.

        Args:
            raster: 2D numpy array containing NaNs or missing values.
            nodata_mask: Optional boolean mask where True indicates missing/invalid pixels.
        """
        if nodata_mask is None:
            nodata_mask = np.isnan(raster) | np.isinf(raster)

        if not np.any(nodata_mask):
            return raster

        if np.all(nodata_mask):
            return np.zeros_like(raster)

        filled = raster.copy()
        # Find nearest valid pixel coordinates via Euclidean Distance Transform
        indices = distance_transform_edt(
            nodata_mask, return_distances=False, return_indices=True
        )
        filled[nodata_mask] = filled[tuple(indices[:, nodata_mask])]

        if method == "gaussian":
            # Apply slight Gaussian smoothing over inpainted boundaries
            smooth = gaussian_filter(filled, sigma=1.0)
            filled[nodata_mask] = smooth[nodata_mask]

        return filled
