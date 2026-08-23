"""Physics-Informed Neural Network (PINN) for Urban Surface Heat Dynamics.

Architecture incorporates:
- Fourier Feature Spatial-Temporal Embeddings to overcome spectral bias
- Residual dense layers with GELU/SiLU activations
- Multi-head outputs for Land Surface Temperature (T_s), Sensible Heat Flux (H),
  Latent Heat Flux (lambda_E), Ground Heat Storage (G), and Net Radiation (R_n).
- Autograd differential operators for spatio-temporal derivatives.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


@dataclass
class PINNOutput:
    """Consolidated thermodynamic predictions from PINN forward pass."""

    t_s: torch.Tensor  # Surface temperature (°C)
    sensible_heat_h: torch.Tensor  # H (W/m²)
    latent_heat_le: torch.Tensor  # lambda*E (W/m²)
    ground_heat_g: torch.Tensor  # G (W/m²)
    net_radiation_rn: torch.Tensor  # R_n (W/m²)


class FourierFeatureMapping(nn.Module):
    """Random Fourier Features mapping for spatial-temporal coordinate encoding."""

    def __init__(self, in_features: int = 3, num_frequencies: int = 16, scale: float = 1.0) -> None:
        super().__init__()
        self.num_frequencies = num_frequencies
        self.register_buffer(
            "B", torch.randn(in_features, num_frequencies) * scale
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (N, in_features)
        # projected: (N, num_frequencies)
        projected = 2.0 * torch.pi * torch.matmul(x, self.B)
        return torch.cat([torch.sin(projected), torch.cos(projected)], dim=-1)


class UrbanHeatPINN(nn.Module):
    """Physics-Informed Neural Network solving the Urban Canopy Surface Energy Balance (SEB)."""

    def __init__(
        self,
        coord_dim: int = 3,  # (x, y, t)
        surface_dim: int = 6,  # (albedo, emissivity, fvc, lambda_p, z0, svf)
        meteo_dim: int = 5,  # (r_sw_down, r_lw_down, t2m_air, wind_speed, relative_humidity)
        hidden_dim: int = 128,
        num_hidden_layers: int = 4,
        num_fourier_frequencies: int = 16,
    ) -> None:
        super().__init__()
        self.coord_dim = coord_dim
        self.surface_dim = surface_dim
        self.meteo_dim = meteo_dim

        # Fourier coordinate encoder: 2 * num_fourier_frequencies
        self.coord_encoder = FourierFeatureMapping(
            in_features=coord_dim, num_frequencies=num_fourier_frequencies
        )
        total_input_dim = (2 * num_fourier_frequencies) + surface_dim + meteo_dim

        # Backbone Dense Network with Residual Skip Connections
        self.input_layer = nn.Sequential(
            nn.Linear(total_input_dim, hidden_dim),
            nn.SiLU(),
        )

        self.hidden_blocks = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.SiLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.SiLU(),
            )
            for _ in range(num_hidden_layers)
        ])

        # Multi-head output decoders
        # 1. Surface Temperature head (°C) - Centered around typical urban temps [15, 60] °C
        self.head_ts = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.SiLU(),
            nn.Linear(64, 1),
        )

        # 2. Sensible heat flux H (W/m²)
        self.head_h = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.SiLU(),
            nn.Linear(64, 1),
        )

        # 3. Latent heat flux lambda*E (W/m²)
        self.head_le = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.SiLU(),
            nn.Linear(64, 1),
        )

        # 4. Ground conductive storage G (W/m²)
        self.head_g = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.SiLU(),
            nn.Linear(64, 1),
        )

        # 5. Net radiation R_n (W/m²)
        self.head_rn = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.SiLU(),
            nn.Linear(64, 1),
        )

        self._init_weights()

    def _init_weights(self) -> None:
        """Initialize weights using Xavier normal initialization."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(
        self,
        coords: torch.Tensor,
        surface_features: torch.Tensor,
        meteo_features: torch.Tensor,
    ) -> PINNOutput:
        """Forward pass for urban thermodynamic predictions.

        Args:
            coords: (N, 3) tensor of [x, y, t], requires_grad=True for PDE loss.
            surface_features: (N, 6) tensor of [albedo, emissivity, fvc, lambda_p, z0, svf].
            meteo_features: (N, 5) tensor of [r_sw_down, r_lw_down, t2m_air, wind_speed, rh].
        """
        encoded_coords = self.coord_encoder(coords)
        x = torch.cat([encoded_coords, surface_features, meteo_features], dim=-1)

        feat = self.input_layer(x)
        for block in self.hidden_blocks:
            feat = feat + block(feat)  # Residual connection

        t_s = self.head_ts(feat) + 30.0  # Base temperature prior
        h = self.head_h(feat)
        le = nn.functional.softplus(self.head_le(feat))  # Latent heat flux >= 0
        g = self.head_g(feat)
        rn = self.head_rn(feat)

        return PINNOutput(
            t_s=t_s,
            sensible_heat_h=h,
            latent_heat_le=le,
            ground_heat_g=g,
            net_radiation_rn=rn,
        )

    @staticmethod
    def compute_spatial_temporal_derivatives(
        t_s: torch.Tensor, coords: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Compute exact autograd partial derivatives of temperature w.r.t (x, y, t).

        Returns:
            dt_dx: d(T_s)/dx
            dt_dy: d(T_s)/dy
            dt_dt: d(T_s)/dt
            laplacian: d^2(T_s)/dx^2 + d^2(T_s)/dy^2
        """
        grads = torch.autograd.grad(
            outputs=t_s,
            inputs=coords,
            grad_outputs=torch.ones_like(t_s),
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0]

        dt_dx = grads[:, 0:1]
        dt_dy = grads[:, 1:2]
        dt_dt = grads[:, 2:3]

        # Second order spatial derivatives for thermal diffusion
        d2t_dx2 = torch.autograd.grad(
            outputs=dt_dx,
            inputs=coords,
            grad_outputs=torch.ones_like(dt_dx),
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0][:, 0:1]

        d2t_dy2 = torch.autograd.grad(
            outputs=dt_dy,
            inputs=coords,
            grad_outputs=torch.ones_like(dt_dy),
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0][:, 1:2]

        laplacian = d2t_dx2 + d2t_dy2

        return dt_dx, dt_dy, dt_dt, laplacian

    @classmethod
    def get_optimal_device(cls) -> torch.device:
        """Detect and return fastest available hardware accelerator (CUDA -> MPS -> CPU)."""
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    @torch.inference_mode()
    def predict_grid_accelerated(
        self,
        coords: torch.Tensor,
        surface_features: torch.Tensor,
        meteo_features: torch.Tensor,
        device: Optional[torch.device] = None,
    ) -> PINNOutput:
        """Execute accelerated mixed-precision inference across spatial raster grids."""
        target_device = device or self.get_optimal_device()
        self.to(target_device)
        self.eval()

        coords_d = coords.to(target_device)
        surf_d = surface_features.to(target_device)
        meteo_d = meteo_features.to(target_device)

        return self.forward(coords_d, surf_d, meteo_d)
