"""PyTorch Training Pipeline and Optimization for Urban Heat PINN.

Features:
- AdamW + Cosine Annealing Learning Rate scheduling
- Spatio-temporal derivative autograd computations for PDE loss
- Checkpoint persistence and validation metrics tracking (RMSE, MAE, SEB Residual)
- Gradient clipping for stable training
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from aerocool_ai.config import Settings, get_settings
from aerocool_ai.core_engine.models.loss_functions import LossBreakdown, PINNCompositeLoss
from aerocool_ai.core_engine.models.pinn_heat_dynamics import UrbanHeatPINN

logger = logging.getLogger(__name__)


@dataclass
class TrainingHistory:
    """Historical loss and metric logs across training epochs."""

    train_losses: List[float]
    val_losses: List[float]
    val_rmse: List[float]
    val_mae: List[float]
    seb_residuals_wm2: List[float]
    best_epoch: int
    best_val_rmse: float


class PINNTrainingPipeline:
    """End-to-end training and evaluation pipeline for Physics-Informed Urban Heat models."""

    def __init__(
        self,
        model: Optional[UrbanHeatPINN] = None,
        settings: Optional[Settings] = None,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        device: Optional[str] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.model = model or UrbanHeatPINN()
        self.model.to(self.device)

        self.loss_fn = PINNCompositeLoss(
            data_weight=self.settings.data_loss_weight,
            physics_weight=self.settings.seb_loss_weight + self.settings.pde_loss_weight,
        ).to(self.device)

        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )

        self.lr_scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.5, patience=10, min_lr=1e-6
        )

    def train_epoch(
        self,
        dataloader: DataLoader,
        compute_pde_derivatives: bool = True,
    ) -> float:
        """Run a single training epoch across batches."""
        self.model.train()
        total_loss = 0.0

        for batch in dataloader:
            coords, surface_feat, meteo_feat, t_target = [
                b.to(self.device) for b in batch
            ]

            if compute_pde_derivatives:
                coords.requires_grad_(True)

            self.optimizer.zero_grad()

            pinn_out = self.model(coords, surface_feat, meteo_feat)

            derivatives = None
            if compute_pde_derivatives:
                derivatives = self.model.compute_spatial_temporal_derivatives(
                    pinn_out.t_s, coords
                )

            breakdown = self.loss_fn(
                pinn_out=pinn_out,
                t_s_target=t_target,
                surface_features=surface_feat,
                meteo_features=meteo_feat,
                derivatives=derivatives,
            )

            breakdown.total_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            total_loss += float(breakdown.total_loss.item())

        return total_loss / max(len(dataloader), 1)

    def evaluate(
        self, dataloader: DataLoader
    ) -> Tuple[float, float, float, float]:
        """Evaluate model on validation/test set.

        Returns: (val_loss, rmse, mae, mean_seb_residual)
        """
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_targets = []
        seb_residuals = []

        with torch.no_grad():
            for batch in dataloader:
                coords, surface_feat, meteo_feat, t_target = [
                    b.to(self.device) for b in batch
                ]

                pinn_out = self.model(coords, surface_feat, meteo_feat)
                breakdown = self.loss_fn(
                    pinn_out=pinn_out,
                    t_s_target=t_target,
                    surface_features=surface_feat,
                    meteo_features=meteo_feat,
                    derivatives=None,
                )

                total_loss += float(breakdown.total_loss.item())
                all_preds.append(pinn_out.t_s.cpu().numpy())
                all_targets.append(t_target.cpu().numpy())

                energy_imbalance = (
                    pinn_out.net_radiation_rn
                    - (
                        pinn_out.ground_heat_g
                        + pinn_out.sensible_heat_h
                        + pinn_out.latent_heat_le
                    )
                )
                seb_residuals.append(torch.abs(energy_imbalance).cpu().numpy())

        preds_arr = np.concatenate(all_preds, axis=0).ravel()
        targets_arr = np.concatenate(all_targets, axis=0).ravel()
        seb_arr = np.concatenate(seb_residuals, axis=0).ravel()

        rmse = float(np.sqrt(np.mean((preds_arr - targets_arr) ** 2)))
        mae = float(np.mean(np.abs(preds_arr - targets_arr)))
        mean_seb = float(np.mean(seb_arr))
        mean_loss = total_loss / max(len(dataloader), 1)

        return mean_loss, rmse, mae, mean_seb

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 50,
        checkpoint_name: str = "urban_heat_pinn_best.pt",
    ) -> TrainingHistory:
        """Execute full model training cycle with early stopping and checkpointing."""
        history = TrainingHistory(
            train_losses=[],
            val_losses=[],
            val_rmse=[],
            val_mae=[],
            seb_residuals_wm2=[],
            best_epoch=0,
            best_val_rmse=float("inf"),
        )

        checkpoint_dir = Path(self.settings.model_checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / checkpoint_name

        for epoch in range(1, epochs + 1):
            train_loss = self.train_epoch(train_loader)
            val_loss, rmse, mae, seb_res = self.evaluate(val_loader)
            self.lr_scheduler.step(val_loss)

            history.train_losses.append(train_loss)
            history.val_losses.append(val_loss)
            history.val_rmse.append(rmse)
            history.val_mae.append(mae)
            history.seb_residuals_wm2.append(seb_res)

            if rmse < history.best_val_rmse:
                history.best_val_rmse = rmse
                history.best_epoch = epoch
                self.save_checkpoint(checkpoint_path)

            if epoch % 10 == 0 or epoch == 1:
                logger.info(
                    f"Epoch {epoch:03d}/{epochs} | Train Loss: {train_loss:.4f} | "
                    f"Val Loss: {val_loss:.4f} | Val RMSE: {rmse:.2f}°C | "
                    f"SEB Imbalance: {seb_res:.1f} W/m²"
                )

        return history

    def save_checkpoint(self, path: Path) -> None:
        """Save model weights and optimizer state to disk."""
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            },
            path,
        )

    def load_checkpoint(self, path: Path) -> None:
        """Load model weights from checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
