"""Parametric Urban Cooling Intervention Simulator.

Simulates thermodynamic changes from spatial cooling interventions:
- Green Roofs (extensive / intensive vegetative layers)
- Cool Roofs (high-albedo reflective coatings)
- Urban Tree Canopy / Street Tree Planting (shading + transpiration)
- Cool / Permeable Pavements (evaporative + reflective surfaces)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class InterventionType(str, Enum):
    """Supported spatial cooling intervention types."""

    GREEN_ROOF = "green_roof"
    COOL_ROOF = "cool_roof"
    URBAN_CANOPY = "urban_canopy"
    COOL_PAVEMENT = "cool_pavement"
    PERMEABLE_PAVEMENT = "permeable_pavement"


@dataclass
class InterventionStrategy:
    """Intervention parameters and thermodynamic modifications."""

    intervention_type: InterventionType
    target_area_fraction: float  # Fraction of eligible surface modified [0.0 - 1.0]
    albedo_delta: float  # Change in surface albedo (e.g. +0.40 for cool roof)
    fvc_delta: float  # Change in vegetation fraction (e.g. +0.70 for green roof)
    cost_per_sqm: float  # Estimated cost in USD / m²
    shading_factor: float = 0.0  # Canopy solar attenuation factor
    evaporative_efficiency: float = 1.0  # Latent heat multiplier


@dataclass
class SimulationResult:
    """Thermodynamic outcome of cooling intervention simulation."""

    baseline_lst: np.ndarray  # Shape (H, W) in °C
    mitigated_lst: np.ndarray  # Shape (H, W) in °C
    delta_lst: np.ndarray  # Cooling benefit (T_base - T_mit) in °C
    mean_cooling_celsius: float
    max_cooling_celsius: float
    modified_albedo: np.ndarray
    modified_fvc: np.ndarray
    intervention_mask: np.ndarray
    total_area_modified_m2: float
    estimated_cost_usd: float
    metadata: Dict[str, Any]


class CoolingInterventionSimulator:
    """Simulates the physical impact of heat mitigation strategies on surface and air temperatures."""

    # Default intervention parameter specifications
    DEFAULTS: Dict[InterventionType, InterventionStrategy] = {
        InterventionType.GREEN_ROOF: InterventionStrategy(
            intervention_type=InterventionType.GREEN_ROOF,
            target_area_fraction=0.80,
            albedo_delta=0.08,
            fvc_delta=0.65,
            cost_per_sqm=120.0,
            evaporative_efficiency=1.8,
        ),
        InterventionType.COOL_ROOF: InterventionStrategy(
            intervention_type=InterventionType.COOL_ROOF,
            target_area_fraction=0.90,
            albedo_delta=0.45,
            fvc_delta=0.0,
            cost_per_sqm=25.0,
            evaporative_efficiency=1.0,
        ),
        InterventionType.URBAN_CANOPY: InterventionStrategy(
            intervention_type=InterventionType.URBAN_CANOPY,
            target_area_fraction=0.40,
            albedo_delta=0.02,
            fvc_delta=0.55,
            cost_per_sqm=65.0,
            shading_factor=0.60,
            evaporative_efficiency=2.2,
        ),
        InterventionType.COOL_PAVEMENT: InterventionStrategy(
            intervention_type=InterventionType.COOL_PAVEMENT,
            target_area_fraction=0.70,
            albedo_delta=0.30,
            fvc_delta=0.0,
            cost_per_sqm=40.0,
            evaporative_efficiency=1.0,
        ),
        InterventionType.PERMEABLE_PAVEMENT: InterventionStrategy(
            intervention_type=InterventionType.PERMEABLE_PAVEMENT,
            target_area_fraction=0.50,
            albedo_delta=0.10,
            fvc_delta=0.10,
            cost_per_sqm=75.0,
            evaporative_efficiency=1.5,
        ),
    }

    def simulate(
        self,
        baseline_lst: np.ndarray,
        albedo_grid: np.ndarray,
        fvc_grid: np.ndarray,
        plan_area_fraction: np.ndarray,
        strategy: InterventionStrategy,
        target_mask: Optional[np.ndarray] = None,
        cell_size_m: float = 30.0,
    ) -> SimulationResult:
        """Simulate microclimatic cooling response from applying an intervention strategy.

        Thermodynamic Principles:
        - Delta LST from Albedo: Delta T_albedo = - (R_sw * Delta alpha) / (4 * eps * sigma * T^3 + rho * cp / r_a)
        - Delta LST from Evapotranspiration: Delta T_fvc = - (lambda * Delta ET) / h_eff
        - Delta LST from Shading: Delta T_shade = - shading_factor * (R_sw / 45.0)
        """
        grid_h, grid_w = baseline_lst.shape

        if target_mask is None:
            # Default target: where urban density is high or heat is elevated
            if strategy.intervention_type in [
                InterventionType.GREEN_ROOF,
                InterventionType.COOL_ROOF,
            ]:
                target_mask = plan_area_fraction > 0.15
            else:
                target_mask = plan_area_fraction < 0.70  # Ground/streets

        # Apply target fraction
        applied_mask = target_mask & (np.random.uniform(0, 1, size=(grid_h, grid_w)) < strategy.target_area_fraction)

        # 1. Albedo modification
        new_albedo = albedo_grid.copy()
        new_albedo[applied_mask] = np.clip(
            new_albedo[applied_mask] + strategy.albedo_delta, 0.05, 0.85
        )

        # 2. Vegetation modification
        new_fvc = fvc_grid.copy()
        new_fvc[applied_mask] = np.clip(
            new_fvc[applied_mask] + strategy.fvc_delta, 0.0, 1.0
        )

        # 3. Thermodynamic temperature drop calculation
        # Typical daytime solar irradiance ~ 750 W/m²
        r_sw = 750.0
        # Effective surface heat transfer coefficient h_c ~ 25 W/(m² K)
        h_c = 25.0

        # Direct solar reflection cooling (°C)
        cooling_albedo = (r_sw * strategy.albedo_delta) / h_c
        # Evapotranspirative latent heat cooling (°C)
        cooling_latent = (strategy.fvc_delta * 65.0 * strategy.evaporative_efficiency) / h_c
        # Canopy shading cooling (°C)
        cooling_shade = (strategy.shading_factor * r_sw) / (h_c * 1.5)

        total_cooling_rate = cooling_albedo + cooling_latent + cooling_shade

        delta_lst = np.zeros_like(baseline_lst)
        delta_lst[applied_mask] = total_cooling_rate

        mitigated_lst = baseline_lst - delta_lst

        # Spatial cost and area calculation
        cell_area_m2 = cell_size_m * cell_size_m
        num_cells_modified = int(np.sum(applied_mask))
        total_area_m2 = num_cells_modified * cell_area_m2
        estimated_cost = total_area_m2 * strategy.cost_per_sqm

        mean_cooling = float(np.mean(delta_lst[applied_mask])) if num_cells_modified > 0 else 0.0
        max_cooling = float(np.max(delta_lst)) if num_cells_modified > 0 else 0.0

        return SimulationResult(
            baseline_lst=baseline_lst,
            mitigated_lst=mitigated_lst,
            delta_lst=delta_lst,
            mean_cooling_celsius=mean_cooling,
            max_cooling_celsius=max_cooling,
            modified_albedo=new_albedo,
            modified_fvc=new_fvc,
            intervention_mask=applied_mask,
            total_area_modified_m2=total_area_m2,
            estimated_cost_usd=estimated_cost,
            metadata={
                "intervention_type": strategy.intervention_type.value,
                "cells_modified": num_cells_modified,
                "cost_per_sqm": strategy.cost_per_sqm,
            },
        )
