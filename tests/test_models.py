"""Unit tests for ML models, PyTorch PINN, and physics-informed loss functions."""

import numpy as np
import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset

from aerocool_ai.core_engine.models.baseline_regressor import LSTBaselineRegressor
from aerocool_ai.core_engine.models.loss_functions import (
    PINNCompositeLoss,
    SurfaceEnergyBalanceLoss,
)
from aerocool_ai.core_engine.models.pinn_heat_dynamics import UrbanHeatPINN
from aerocool_ai.core_engine.models.train_pipeline import PINNTrainingPipeline


def test_baseline_regressor():
    """Test XGBoost/RF baseline regressor fitting and inference."""
    X = np.random.randn(100, 15)
    # Synthetic target with strong dependence on first feature (NDVI)
    y = 30.0 - 5.0 * X[:, 0] + np.random.normal(0, 0.5, 100)

    regressor = LSTBaselineRegressor(model_type="xgboost", n_estimators=20)
    regressor.fit(X, y)

    metrics = regressor.evaluate(X, y)
    assert metrics.rmse < 2.5
    assert metrics.r2 > 0.6
    assert len(metrics.feature_importances) == 15


def test_urban_heat_pinn_forward_and_autograd():
    """Test PyTorch UrbanHeatPINN forward propagation and spatial-temporal gradient calculations."""
    batch_size = 16
    coords = torch.randn(batch_size, 3, requires_grad=True)  # (x, y, t)
    surface = torch.rand(batch_size, 6)  # (albedo, eps, fvc, lambda_p, z0, svf)
    meteo = torch.rand(batch_size, 5)  # (r_sw, r_lw, t2m, u, rh)

    model = UrbanHeatPINN()
    output = model(coords, surface, meteo)

    assert output.t_s.shape == (batch_size, 1)
    assert output.sensible_heat_h.shape == (batch_size, 1)
    assert output.latent_heat_le.shape == (batch_size, 1)
    assert output.ground_heat_g.shape == (batch_size, 1)
    assert output.net_radiation_rn.shape == (batch_size, 1)

    # Test autograd partial derivatives
    dt_dx, dt_dy, dt_dt, laplacian = model.compute_spatial_temporal_derivatives(
        output.t_s, coords
    )
    assert dt_dx.shape == (batch_size, 1)
    assert dt_dy.shape == (batch_size, 1)
    assert dt_dt.shape == (batch_size, 1)
    assert laplacian.shape == (batch_size, 1)


def test_surface_energy_balance_loss():
    """Test first-principles physics conservation loss computation."""
    loss_fn = SurfaceEnergyBalanceLoss()

    batch_size = 8
    t_s = torch.full((batch_size, 1), 35.0)
    h = torch.full((batch_size, 1), 150.0)
    le = torch.full((batch_size, 1), 200.0)
    g = torch.full((batch_size, 1), 50.0)
    rn = torch.full((batch_size, 1), 400.0)  # rn = h + le + g -> perfect balance

    surface = torch.rand(batch_size, 6)
    meteo = torch.rand(batch_size, 5)

    physics_loss, metrics = loss_fn(t_s, h, le, g, rn, surface, meteo)
    assert physics_loss.item() >= 0.0
    assert "mean_energy_imbalance_wm2" in metrics
    assert np.isclose(metrics["mean_energy_imbalance_wm2"].item(), 0.0, atol=1e-4)


def test_pinn_training_pipeline_epoch():
    """Test complete training epoch on small synthetic dataset."""
    N = 32
    coords = torch.randn(N, 3)
    surface = torch.rand(N, 6)
    meteo = torch.rand(N, 5)
    t_target = torch.full((N, 1), 32.0)

    dataset = TensorDataset(coords, surface, meteo, t_target)
    loader = DataLoader(dataset, batch_size=8)

    pipeline = PINNTrainingPipeline(device="cpu")
    loss = pipeline.train_epoch(loader, compute_pde_derivatives=True)
    assert loss > 0.0

    val_loss, rmse, mae, seb = pipeline.evaluate(loader)
    assert rmse >= 0.0
    assert mae >= 0.0
