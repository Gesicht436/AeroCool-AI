"""Baseline Gradient Boosted (XGBoost) and Random Forest LST Regressors.

Provides benchmark empirical regression mapping geospatial covariates
(NDVI, NDBI, Albedo, SVF, Building Density, Meteo) to Land Surface Temperature (LST).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
import xgboost as xgb

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "ndvi",
    "ndbi",
    "ndwi",
    "albedo",
    "fvc",
    "emissivity",
    "sky_view_factor",
    "impervious_fraction",
    "building_height",
    "plan_area_fraction",
    "t2m_air",
    "r_sw_down",
    "r_lw_down",
    "wind_speed",
    "relative_humidity",
]


@dataclass
class BaselineEvaluationMetrics:
    """Evaluation metrics container for baseline models."""

    rmse: float
    mae: float
    r2: float
    feature_importances: Dict[str, float]
    sample_count: int


class LSTBaselineRegressor:
    """Empirical machine learning baseline for urban heat driver quantification."""

    def __init__(
        self,
        model_type: str = "xgboost",
        n_estimators: int = 200,
        max_depth: int = 6,
        learning_rate: float = 0.05,
        random_state: int = 42,
    ) -> None:
        self.model_type = model_type
        self.random_state = random_state
        self.feature_names = FEATURE_NAMES

        if model_type == "xgboost":
            self.model = xgb.XGBRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=random_state,
                n_jobs=-1,
                tree_method="hist",
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1,
            )

        self._is_fitted = False

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        eval_set: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    ) -> "LSTBaselineRegressor":
        """Fit the regressor on tabular feature matrix X and target LST y.

        Args:
            X: Array of shape (N, num_features)
            y: Target LST in Celsius of shape (N,)
            eval_set: Optional (X_val, y_val) validation set
        """
        # Ensure 2D
        if X.ndim != 2:
            raise ValueError(f"Expected 2D feature matrix X, got shape {X.shape}")
        if y.ndim != 1:
            y = y.ravel()

        if self.model_type == "xgboost" and eval_set is not None:
            self.model.fit(
                X,
                y,
                eval_set=[eval_set],
                verbose=False,
            )
        else:
            self.model.fit(X, y)

        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict LST values (°C) for given feature matrix."""
        if not self._is_fitted:
            raise RuntimeError("Model has not been trained yet. Call fit() first.")
        return self.model.predict(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> BaselineEvaluationMetrics:
        """Evaluate model predictions against ground truth LST."""
        y_pred = self.predict(X)
        rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
        mae = float(mean_absolute_error(y, y_pred))
        r2 = float(r2_score(y, y_pred))

        importances = {}
        if hasattr(self.model, "feature_importances_"):
            raw_imp = self.model.feature_importances_
            for i, name in enumerate(self.feature_names[: X.shape[1]]):
                importances[name] = float(raw_imp[i])

        return BaselineEvaluationMetrics(
            rmse=rmse,
            mae=mae,
            r2=r2,
            feature_importances=importances,
            sample_count=len(y),
        )

    def predict_spatial_grid(
        self,
        feature_maps: Dict[str, np.ndarray],
        spatial_shape: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        """Run batch inference on 2D spatial feature rasters."""
        channels = []
        for name in self.feature_names:
            if name in feature_maps:
                channels.append(feature_maps[name].ravel())
            else:
                # Default fallback value
                first_arr = next(iter(feature_maps.values()))
                channels.append(np.zeros_like(first_arr).ravel())

        X_flat = np.column_stack(channels)
        y_pred_flat = self.predict(X_flat)

        if spatial_shape is None:
            first_arr = next(iter(feature_maps.values()))
            spatial_shape = first_arr.shape

        return y_pred_flat.reshape(spatial_shape)
