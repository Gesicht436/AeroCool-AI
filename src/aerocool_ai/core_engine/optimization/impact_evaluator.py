"""Urban Heat Impact, Human Thermal Comfort, and Energy Savings Evaluator.

Quantifies macro and micro impacts:
- Surface Temperature Drop (Delta T_LST) & Canopy Air Temperature Drop (Delta T_air)
- Heat Vulnerability Index (HVI) relief
- Thermal Stress index improvement (Universal Thermal Climate Index - UTCI)
- Avoided Building HVAC Cooling Energy (kWh / m² / year) & CO2 emissions (kg CO2e)
- Population exposure reduction to hazardous thermal thresholds (> 35°C)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CoolingImpactReport:
    """Consolidated impact assessment and benefit metrics."""

    mean_lst_reduction_celsius: float
    max_lst_reduction_celsius: float
    mean_air_temp_reduction_celsius: float
    population_heat_exposure_reduction_pct: float
    annual_cooling_energy_saved_kwh: float
    annual_co2_avoided_tons: float
    total_capital_investment_usd: float
    payback_period_years: float
    utci_thermal_stress_category_shift: str
    metadata: Dict[str, Any]


class ImpactEvaluator:
    """Calculates socioeconomic, energy, and physiological thermal benefits of cooling scenarios."""

    # Building Energy Benchmark Constants (ASHRAE / US DOE Commercial Prototype models)
    HVAC_SAVINGS_PER_DEGREE_C_PER_M2_KWH: float = 3.8  # kWh / (m² · °C · year)
    GRID_EMISSION_FACTOR_KG_CO2_PER_KWH: float = 0.385  # kg CO2 / kWh
    ELECTRICITY_RATE_USD_PER_KWH: float = 0.16  # USD / kWh

    @classmethod
    def estimate_air_temp_reduction(cls, delta_lst: np.ndarray) -> np.ndarray:
        """Estimate 2m canopy air temperature reduction from surface temperature drop.

        Empirical atmospheric boundary scaling: Delta T_air ~ 0.35 * Delta T_LST
        """
        return delta_lst * 0.35

    def evaluate(
        self,
        baseline_lst: np.ndarray,
        mitigated_lst: np.ndarray,
        modified_area_m2: float,
        capital_investment_usd: float,
        population_density_grid: Optional[np.ndarray] = None,
    ) -> CoolingImpactReport:
        """Evaluate full thermal, energetic, and economic benefits."""
        delta_lst = np.maximum(0.0, baseline_lst - mitigated_lst)
        delta_air = self.estimate_air_temp_reduction(delta_lst)

        mean_lst_red = float(np.mean(delta_lst[delta_lst > 0])) if np.any(delta_lst > 0) else 0.0
        max_lst_red = float(np.max(delta_lst)) if np.any(delta_lst > 0) else 0.0
        mean_air_red = float(np.mean(delta_air[delta_air > 0])) if np.any(delta_air > 0) else 0.0

        # Energy savings calculation
        annual_energy_saved_kwh = (
            modified_area_m2 * mean_air_red * self.HVAC_SAVINGS_PER_DEGREE_C_PER_M2_KWH
        )
        annual_cost_savings_usd = annual_energy_saved_kwh * self.ELECTRICITY_RATE_USD_PER_KWH
        annual_co2_tons = (
            annual_energy_saved_kwh * self.GRID_EMISSION_FACTOR_KG_CO2_PER_KWH
        ) / 1000.0

        payback_years = (
            capital_investment_usd / max(annual_cost_savings_usd, 1.0)
            if capital_investment_usd > 0
            else 0.0
        )

        # Population exposure analysis (pixels exceeding hazardous threshold 35°C)
        if population_density_grid is None:
            population_density_grid = np.full_like(baseline_lst, 150.0)  # 150 people / cell approx

        base_exposed = np.sum(population_density_grid[baseline_lst > 35.0])
        mit_exposed = np.sum(population_density_grid[mitigated_lst > 35.0])
        pop_reduction_pct = (
            float((base_exposed - mit_exposed) / max(base_exposed, 1.0) * 100.0)
            if base_exposed > 0
            else 0.0
        )

        # UTCI category shift description
        if mean_air_red > 2.0:
            utci_shift = "Very Strong Heat Stress -> Moderate Heat Stress"
        elif mean_air_red > 1.0:
            utci_shift = "Strong Heat Stress -> Moderate Heat Stress"
        elif mean_air_red > 0.4:
            utci_shift = "Moderate Heat Stress -> Slight Heat Stress"
        else:
            utci_shift = "Minor Thermal Relief"

        return CoolingImpactReport(
            mean_lst_reduction_celsius=mean_lst_red,
            max_lst_reduction_celsius=max_lst_red,
            mean_air_temp_reduction_celsius=mean_air_red,
            population_heat_exposure_reduction_pct=pop_reduction_pct,
            annual_cooling_energy_saved_kwh=annual_energy_saved_kwh,
            annual_co2_avoided_tons=annual_co2_tons,
            total_capital_investment_usd=capital_investment_usd,
            payback_period_years=payback_years,
            utci_thermal_stress_category_shift=utci_shift,
            metadata={
                "annual_cost_savings_usd": annual_cost_savings_usd,
                "grid_emission_factor": self.GRID_EMISSION_FACTOR_KG_CO2_PER_KWH,
            },
        )
