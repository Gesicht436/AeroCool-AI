# Test Suite (`tests/`)

This directory contains the automated test suite for **AeroCool-AI**, covering configuration, remote sensing ingestion, preprocessing, physics-informed machine learning, spatial optimization, and FastAPI REST endpoints.

---

## Test Organization

```text
tests/
├── conftest.py              # Pytest async test client and global fixtures
├── test_config.py           # Settings validation and caching tests
├── test_ingestion.py        # Landsat, ECOSTRESS, Sentinel, ERA5, OSM ingestion tests
├── test_preprocessing.py    # Spatial alignment, raster scaling, and biophysical index tests
├── test_models.py           # XGBoost baseline, PyTorch PINN, autograd & SEB loss tests
├── test_optimization.py     # Cooling simulator, spatial allocator, and impact evaluator tests
└── test_api.py              # FastAPI endpoint integration tests
```

---

## Files in this Directory

### 1. [`conftest.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/conftest.py)
- **Role**: Global test configuration and fixtures.
- **Fixtures**:
  - `async_client`: Asynchronous `httpx.AsyncClient` wired to the FastAPI `app` via `ASGITransport` for fast, in-process HTTP endpoint testing without requiring a live network socket.

---

### 2. [`test_config.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_config.py)
- **Role**: Validates application settings, default values, dynamic property formatting (DSN strings), and `@lru_cache` singleton stability.
- **Key Tests**:
  - `test_settings_defaults`: Checks default ports, API prefixes, async database URLs, and loss weights.
  - `test_get_settings_cached`: Ensures `get_settings()` returns identical singleton instances.

---

### 3. [`test_ingestion.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_ingestion.py)
- **Role**: Verifies remote sensing and urban morphology data acquisition collectors.
- **Key Tests**:
  - `test_landsat_thermal_scaling`: Validates Landsat digital number to Celsius radiometric conversion.
  - `test_landsat_collector_fetch`: Tests AOI bounding box queries and output raster formats.
  - `test_ecostress_collector_diurnal`: Verifies diurnal temperature dynamics across morning, solar noon, and nocturnal passes.
  - `test_sentinel_lulc_collector`: Verifies multispectral reflectance band extraction and LULC class generation.
  - `test_era5_meteo_collector`: Tests atmospheric boundary condition grids and Magnus-Tetens relative humidity calculations.
  - `test_osm_morphology_collector`: Tests 3D building height aggregation and aerodynamic roughness length ($z_0$) computation.

---

### 4. [`test_preprocessing.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_preprocessing.py)
- **Role**: Verifies raster grid alignment, normalization scaling, and biophysical feature extraction.
- **Key Tests**:
  - `test_spatial_alignment_resample`: Tests multi-layer continuous/categorical resampling and tensor stacking.
  - `test_raster_normalizer_scaling_and_inpaint`: Validates MinMax scaling and Euclidean Distance Transform NoData inpainting.
  - `test_urban_feature_extractor`: Verifies NDVI, NDBI, NDWI, Liang broadband albedo, FVC, Sobrino emissivity, and Sky View Factor calculations.

---

### 5. [`test_models.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_models.py)
- **Role**: Tests empirical ML regressors, PyTorch PINN forward passes, autograd gradient operators, and physics loss functions.
- **Key Tests**:
  - `test_baseline_regressor`: Verifies XGBoost model fitting, metric evaluation (RMSE, $R^2$), and feature importances.
  - `test_urban_heat_pinn_forward_and_autograd`: Validates PyTorch `UrbanHeatPINN` tensor outputs and autograd partial derivatives ($\frac{\partial T_s}{\partial t}, \nabla^2 T_s$).
  - `test_surface_energy_balance_loss`: Tests physics energy conservation residual calculation ($R_n - G - H - \lambda E = 0$).
  - `test_pinn_training_pipeline_epoch`: Runs training epochs and validation evaluation cycles.

---

### 6. [`test_optimization.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_optimization.py)
- **Role**: Tests parametric cooling simulations, spatial knapsack allocation solvers, and impact assessment.
- **Key Tests**:
  - `test_cooling_simulator_green_roof`: Verifies temperature drops and cost estimation from green roof interventions.
  - `test_spatial_allocation_solver`: Tests budget constraint enforcement ($\sum c_k x_{ik} \le \text{Budget}$) and parcel prioritization.
  - `test_impact_evaluator`: Tests avoided cooling energy ($\text{kWh}$), avoided $\text{CO}_2$ emissions, and payback period calculations.

---

### 7. [`test_api.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_api.py)
- **Role**: Full asynchronous integration tests for FastAPI REST endpoints.
- **Key Tests**:
  - `test_health_endpoint`: `GET /health` system liveness check.
  - `test_hotspot_detection_endpoint`: `POST /api/v1/hotspots/detect` GeoJSON response validation.
  - `test_hotspot_diagnostics_endpoint`: `GET /api/v1/hotspots/{hotspot_id}`.
  - `test_optimization_allocation_endpoint`: `POST /api/v1/optimization/allocate`.
  - `test_pareto_frontier_endpoint`: `POST /api/v1/optimization/pareto`.
  - `test_simulation_run_endpoint_with_mock_db`: `POST /api/v1/simulation/run` with mock database dependency injection.

---

## Running the Tests

```bash
# Run full test suite via uv
uv run pytest -v

# Run a specific test module
uv run pytest tests/test_models.py -v

# Run with test coverage
uv run pytest --cov=aerocool_ai tests/
```
