# Core Remote Sensing and Machine Learning Engine (`src/aerocool_ai/core_engine/`)

The `core_engine` package is the scientific and computational backbone of **AeroCool-AI**. It combines satellite Earth observation, 3D urban canopy morphology, fluid/thermal physics, and constrained mathematical optimization.

---

## Architecture and Data Flow

```mermaid
flowchart LR
    subgraph S1 [1. Ingestion]
        A[Landsat 8/9 LST]
        B[ECOSTRESS Diurnal LST]
        C[Sentinel-2 Reflectance & LULC]
        D[ERA5 Atmospheric Forcings]
        E[OSM 3D Buildings & Morphology]
    end

    subgraph S2 [2. Preprocessing]
        F[Spatial Alignment & Grid Matching]
        G[Raster Normalization & Inpainting]
        H[Biophysical Indices: NDVI, NDBI, Albedo, SVF]
    end

    subgraph S3 [3. Models]
        I[XGBoost Empirical Baseline]
        J[UrbanHeatPINN Neural Network]
        K[Surface Energy Balance Loss]
    end

    subgraph S4 [4. Optimization]
        L[Cooling Intervention Simulator]
        M[Spatial Allocation Solver]
        N[Thermal & Energy Impact Evaluator]
    end

    S1 --> S2 --> S3 --> S4
```

---

## Files in this Directory

### [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/__init__.py)
- **Role**: Exports the four primary submodules of the core engine: `ingestion`, `preprocessing`, `models`, and `optimization`.
- **Exposed Namespaces**:
  - `ingestion`: Satellite and meteorological data collectors.
  - `preprocessing`: Alignment, normalization, and feature extraction.
  - `models`: Empirical and Physics-Informed Neural Networks.
  - `optimization`: Parametric simulation and spatial allocation solvers.

---

## Sub-Packages Breakdown

### 1. [`ingestion/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/ingestion/README.md)
Contains dedicated data acquisition collectors for remote sensing, climate reanalysis, and urban morphology:
- **`gee_landsat_collector.py`**: Queries Landsat 8/9 Collection 2 Level-2 Surface Temperature via Google Earth Engine with QA_PIXEL bitmask cloud screening and radiometric calibration.
- **`ecostress_collector.py`**: Extracts diurnal thermal dynamics (morning, solar noon, afternoon, night) from NASA's ECOSTRESS sensor on the ISS.
- **`sentinel_lulc_collector.py`**: Ingests Sentinel-2 multispectral reflectance (Bands 2, 3, 4, 8, 11, 12) and 10m Land Use / Land Cover (LULC) categorical grids.
- **`era5_meteo_collector.py`**: Ingests hourly meteorological boundary conditions ($T_{2m}$, $R_{sw\downarrow}$, $R_{lw\downarrow}$, $u_{10}$, $\text{RH}$, $P_s$).
- **`osm_morphology_collector.py`**: Extracts 3D building heights, building plan area fraction ($\lambda_p$), aerodynamic roughness ($z_0$), and street canyon metrics using OSMnx/Overpass.

### 2. [`preprocessing/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/preprocessing/README.md)
Standardizes heterogeneous spatial layers:
- **`spatial_alignment.py`**: Reprojection, clipping, and spatial resampling across disparate spatial resolutions (10m, 30m, 70m, 0.1°).
- **`raster_normalizer.py`**: MinMax, Z-score, and Robust quantile standardizers with Euclidean Distance Transform (EDT) NoData inpainting.
- **`feature_extractor.py`**: Computes biophysical indices: $\text{NDVI}$, $\text{NDBI}$, $\text{NDWI}$, Liang (2001) broadband shortwave albedo ($\alpha$), Fractional Vegetation Cover ($\text{FVC}$), thermal emissivity ($\varepsilon$), and Sky View Factor ($\text{SVF}$).

### 3. [`models/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/models/README.md)
AI/ML models bridging empirical observation and thermodynamic physics:
- **`baseline_regressor.py`**: Gradient boosted decision trees (XGBoost) and Random Forests for feature importance ranking.
- **`pinn_heat_dynamics.py`**: PyTorch neural network featuring Random Fourier Feature coordinate encodings, residual skip connections, multi-head thermodynamic flux predictions, and autograd spatio-temporal differential operators.
- **`loss_functions.py`**: Encodes the Surface Energy Balance (SEB) conservation law ($R_n - G - H - \lambda E = 0$), Stefan-Boltzmann radiative equilibrium, bulk aerodynamic sensible heat flux, and 2D advection-diffusion PDE residuals.
- **`train_pipeline.py`**: Training loop with AdamW optimizer, LR schedulers, checkpoint persistence, and validation metric tracking.

### 4. [`optimization/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/optimization/README.md)
Urban microclimate intervention and strategy optimization:
- **`cooling_simulator.py`**: Simulates the physical thermodynamic response of green roofs, cool roofs, urban tree canopies, and cool/permeable pavements.
- **`spatial_allocator.py`**: Solves multi-objective constrained spatial allocation problems under capital budgets and Heat Vulnerability Index (HVI) constraints, producing Pareto efficiency curves.
- **`impact_evaluator.py`**: Quantifies temperature reductions ($\Delta T_{\text{LST}}$, $\Delta T_{\text{air}}$), UTCI thermal comfort category shifts, avoided building HVAC cooling electricity ($\text{kWh}/\text{year}$), and avoided $\text{CO}_2$ emissions.

---

## End-to-End Pipeline Example

```python
from aerocool_ai.core_engine.ingestion import LandsatLSTCollector, OSMMorphologyCollector
from aerocool_ai.core_engine.preprocessing import UrbanFeatureExtractor
from aerocool_ai.core_engine.optimization import SpatialAllocationSolver, InterventionType

# 1. Ingestion
bbox = (-74.02, 40.70, -73.95, 40.78)
lst_res = LandsatLSTCollector().fetch_lst_aoi(bbox, "2026-06-01", "2026-08-31")
morph_res = OSMMorphologyCollector().fetch_morphology(bbox, grid_shape=lst_res.data.shape)

# 2. Optimization
solver = SpatialAllocationSolver()
plan = solver.solve(
    baseline_lst=lst_res.data,
    albedo_grid=np.full_like(lst_res.data, 0.12),
    fvc_grid=np.full_like(lst_res.data, 0.10),
    plan_area_fraction=morph_res.plan_area_fraction,
    budget_usd=500_000.0,
    allowed_strategies=[InterventionType.COOL_ROOF, InterventionType.GREEN_ROOF],
)

print(f"Total spent: ${plan.total_spent_usd:,.2f}")
print(f"Mean cooling achieved: {plan.mean_cooling_celsius:.2f} °C")
```
