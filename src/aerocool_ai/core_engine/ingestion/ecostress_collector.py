"""NASA ECOSTRESS Diurnal Land Surface Temperature Ingestion.

ECOSTRESS captures diurnal thermal dynamics (morning, midday, afternoon, and nocturnal passes)
at high spatial resolution (70m) from the International Space Station (ISS).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from aerocool_ai.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class ECOSTRESSObservation:
    """Container for ECOSTRESS LST granule data."""

    data: np.ndarray  # Temperature in Celsius, Shape (H, W)
    quality_flag: np.ndarray  # QC mask
    overpass_time: datetime
    local_solar_time_hours: float  # e.g., 14.5 for 2:30 PM
    bounds: Tuple[float, float, float, float]
    resolution_m: float
    granule_id: str
    metadata: Dict[str, Any]


class ECOSTRESSCollector:
    """Collector for NASA LP DAAC ECOSTRESS L2/L3 Land Surface Temperature & Emissivity (ECO2LSTE)."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def fetch_diurnal_passes(
        self,
        bbox: Tuple[float, float, float, float],
        date_str: str,
        target_hours: Optional[List[float]] = None,
    ) -> List[ECOSTRESSObservation]:
        """Fetch diurnal LST observations for an AOI on a given date across different times of day."""
        if target_hours is None:
            # Default diurnal sampling: Morning (09:00), Solar Noon (13:00), Afternoon Peak (16:00), Night (22:00)
            target_hours = [9.0, 13.0, 16.0, 22.0]

        observations: List[ECOSTRESSObservation] = []
        for hour in target_hours:
            obs = self._simulate_or_fetch_pass(bbox, date_str, hour)
            observations.append(obs)

        return observations

    def _simulate_or_fetch_pass(
        self,
        bbox: Tuple[float, float, float, float],
        date_str: str,
        hour: float,
    ) -> ECOSTRESSObservation:
        """Simulate or fetch ECOSTRESS temperature field with diurnal physics dynamics."""
        min_lon, min_lat, max_lon, max_lat = bbox
        grid_h, grid_w = 64, 64

        y = np.linspace(-2, 2, grid_h)
        x = np.linspace(-2, 2, grid_w)
        xx, yy = np.meshgrid(x, y)

        # Diurnal temperature cycle: T(t) = T_mean + T_amp * sin((t - 9) * pi / 12)
        # Peak heat around 14:00 - 16:00
        diurnal_factor = np.sin((hour - 8.0) * np.pi / 14.0) if 6.0 <= hour <= 20.0 else -0.5
        diurnal_factor = max(diurnal_factor, -0.7)

        ambient_base = 24.0 + 10.0 * diurnal_factor
        # Urban canopy thermal mass retains heat late into the evening (UHI nocturnal effect)
        thermal_inertia_lag = 3.5 if hour >= 18.0 or hour <= 6.0 else 0.0
        uhi_intensity = (4.0 * np.exp(-(xx**2 + yy**2) / 1.8)) + thermal_inertia_lag

        surface_temp = ambient_base + uhi_intensity + np.random.normal(0, 0.25, size=(grid_h, grid_w))
        qc_flags = np.zeros((grid_h, grid_w), dtype=np.uint8)  # 0: Best Quality

        granule_id = f"ECO2LSTE_{date_str.replace('-', '')}_{int(hour):02d}00_001"

        return ECOSTRESSObservation(
            data=surface_temp.astype(np.float32),
            quality_flag=qc_flags,
            overpass_time=datetime.fromisoformat(f"{date_str}T{int(hour):02d}:{int((hour%1)*60):02d}:00"),
            local_solar_time_hours=hour,
            bounds=bbox,
            resolution_m=70.0,
            granule_id=granule_id,
            metadata={"source": "NASA_LP_DAAC_ECOSTRESS", "simulated": True},
        )
