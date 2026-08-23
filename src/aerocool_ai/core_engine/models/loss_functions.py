"""Physics-Informed Loss Functions for Urban Surface Energy Balance (SEB).

Encodes first-principles thermodynamics:
- Surface Energy Balance Conservation: R_n - G - H - lambda_E = 0
- Stefan-Boltzmann Radiative Equilibrium: R_n = (1 - alpha)*R_sw_down + eps*R_lw_down - eps*sigma*(T_s+273.15)^4
- Bulk Aerodynamic Sensible Heat Exchange: H = rho * c_p * (T_s - T_a) / r_a
- Transient 2D Advection-Diffusion Thermal PDE Residual
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Tuple

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


@dataclass
class LossBreakdown:
    """Detailed breakdown of individual physics and data loss components."""

    total_loss: torch.Tensor
    data_loss: torch.Tensor
    seb_balance_loss: torch.Tensor
    radiation_law_loss: torch.Tensor
    sensible_heat_loss: torch.Tensor
    pde_residual_loss: torch.Tensor


class SurfaceEnergyBalanceLoss(nn.Module):
    """Calculates the physical energy conservation residual across urban surfaces."""

    # Physical Constants
    STEFAN_BOLTZMANN_SIGMA: float = 5.670374419e-8  # W/(m² K⁴)
    AIR_DENSITY_RHO: float = 1.205  # kg/m³ at 20°C
    SPECIFIC_HEAT_CP: float = 1005.0  # J/(kg K)
    VON_KARMAN_KAPPA: float = 0.40  # Dimensionless
    EFFECTIVE_HEAT_CAPACITY: float = 1.8e6  # J/(m³ K) for urban asphalt/concrete composite
    THERMAL_DIFFUSIVITY: float = 0.8e-6  # m²/s

    def __init__(
        self,
        seb_weight: float = 0.35,
        rad_weight: float = 0.20,
        sensible_weight: float = 0.20,
        pde_weight: float = 0.25,
    ) -> None:
        super().__init__()
        self.seb_weight = seb_weight
        self.rad_weight = rad_weight
        self.sensible_weight = sensible_weight
        self.pde_weight = pde_weight

    def calculate_aerodynamic_resistance(
        self, wind_speed: torch.Tensor, z0: torch.Tensor, measurement_height_z: float = 10.0
    ) -> torch.Tensor:
        """Compute aerodynamic resistance to heat transfer r_a (s/m).

        Formula:
            r_a = (ln(z / z_0))^2 / (kappa^2 * u)
        """
        u_safe = torch.clamp(wind_speed, min=0.5)
        z0_safe = torch.clamp(z0, min=0.01, max=measurement_height_z * 0.5)
        log_term = torch.log(measurement_height_z / z0_safe)
        r_a = (log_term ** 2) / ((self.VON_KARMAN_KAPPA ** 2) * u_safe)
        return torch.clamp(r_a, min=5.0, max=500.0)

    def calculate_physical_radiation(
        self,
        t_s_celsius: torch.Tensor,
        albedo: torch.Tensor,
        emissivity: torch.Tensor,
        r_sw_down: torch.Tensor,
        r_lw_down: torch.Tensor,
    ) -> torch.Tensor:
        """Calculate theoretical Net Radiation R_n using Stefan-Boltzmann law.

        R_n = (1 - alpha) * R_sw_down + eps * R_lw_down - eps * sigma * (T_s + 273.15)^4
        """
        t_kelvin = t_s_celsius + 273.15
        absorbed_solar = (1.0 - albedo) * r_sw_down
        absorbed_longwave = emissivity * r_lw_down
        emitted_longwave = emissivity * self.STEFAN_BOLTZMANN_SIGMA * (t_kelvin ** 4)

        return absorbed_solar + absorbed_longwave - emitted_longwave

    def forward(
        self,
        t_s: torch.Tensor,
        h: torch.Tensor,
        le: torch.Tensor,
        g: torch.Tensor,
        rn: torch.Tensor,
        surface_features: torch.Tensor,
        meteo_features: torch.Tensor,
        derivatives: Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """Compute all physical constraint losses.

        surface_features: [albedo, emissivity, fvc, lambda_p, z0, svf]
        meteo_features: [r_sw_down, r_lw_down, t2m_air, wind_speed, rh]
        """
        albedo = surface_features[:, 0:1]
        emissivity = surface_features[:, 1:2]
        z0 = surface_features[:, 4:5]

        r_sw_down = meteo_features[:, 0:1]
        r_lw_down = meteo_features[:, 1:2]
        t2m_air = meteo_features[:, 2:3]
        wind_speed = meteo_features[:, 3:4]

        # 1. Surface Energy Balance Residual: R_n - (G + H + lambda_E) = 0
        energy_residual = rn - (g + h + le)
        seb_loss = torch.mean(energy_residual ** 2)

        # 2. Stefan-Boltzmann Net Radiation Residual
        rn_theoretical = self.calculate_physical_radiation(
            t_s, albedo, emissivity, r_sw_down, r_lw_down
        )
        rad_loss = torch.mean((rn - rn_theoretical) ** 2)

        # 3. Aerodynamic Sensible Heat Exchange Residual
        r_a = self.calculate_aerodynamic_resistance(wind_speed, z0)
        h_theoretical = (self.AIR_DENSITY_RHO * self.SPECIFIC_HEAT_CP * (t_s - t2m_air)) / r_a
        sensible_loss = torch.mean((h - h_theoretical) ** 2)

        # 4. Spatiotemporal PDE Residual (if derivatives provided)
        if derivatives is not None:
            dt_dx, dt_dy, dt_dt, laplacian = derivatives
            # Advection-diffusion heat equation: dT/dt = D * laplacian(T) - u * grad(T) + Source
            # Scaled to urban canopy scale (dt in hours -> seconds conversion factor 3600)
            pde_res = dt_dt - (self.THERMAL_DIFFUSIVITY * laplacian * 1e4) - (energy_residual / 100.0)
            pde_loss = torch.mean(pde_res ** 2)
        else:
            pde_loss = torch.tensor(0.0, device=t_s.device)

        total_physics_loss = (
            self.seb_weight * seb_loss
            + self.rad_weight * rad_loss
            + self.sensible_weight * sensible_loss
            + self.pde_weight * pde_loss
        )

        metrics = {
            "seb_loss": seb_loss.detach(),
            "rad_loss": rad_loss.detach(),
            "sensible_loss": sensible_loss.detach(),
            "pde_loss": pde_loss.detach(),
            "mean_energy_imbalance_wm2": torch.mean(torch.abs(energy_residual)).detach(),
        }

        return total_physics_loss, metrics


class PINNCompositeLoss(nn.Module):
    """Combines supervised observational loss (MSE) and thermodynamic physics losses."""

    def __init__(
        self,
        data_weight: float = 0.40,
        physics_weight: float = 0.60,
    ) -> None:
        super().__init__()
        self.data_weight = data_weight
        self.physics_weight = physics_weight
        self.physics_loss_fn = SurfaceEnergyBalanceLoss()
        self.mse_fn = nn.MSELoss()

    def forward(
        self,
        pinn_out: Any,
        t_s_target: torch.Tensor,
        surface_features: torch.Tensor,
        meteo_features: torch.Tensor,
        derivatives: Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]] = None,
    ) -> LossBreakdown:
        """Compute composite weighted multi-objective loss."""
        data_loss = self.mse_fn(pinn_out.t_s, t_s_target)

        physics_loss, metrics = self.physics_loss_fn(
            t_s=pinn_out.t_s,
            h=pinn_out.sensible_heat_h,
            le=pinn_out.latent_heat_le,
            g=pinn_out.ground_heat_g,
            rn=pinn_out.net_radiation_rn,
            surface_features=surface_features,
            meteo_features=meteo_features,
            derivatives=derivatives,
        )

        total = self.data_weight * data_loss + self.physics_weight * physics_loss

        return LossBreakdown(
            total_loss=total,
            data_loss=data_loss,
            seb_balance_loss=metrics["seb_loss"],
            radiation_law_loss=metrics["rad_loss"],
            sensible_heat_loss=metrics["sensible_loss"],
            pde_residual_loss=metrics["pde_loss"],
        )
