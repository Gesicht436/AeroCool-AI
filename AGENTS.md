# AGENTS.md: AeroCool-AI System & Context Guide for Autonomous AI Agents

> **Target Audience:** Autonomous Coding Agents, LLM Pair Programmers, and Technical Contributors.  
> **Last Updated:** August 2026 | **Project Version:** `0.1.0` | **Status:** Core Architecture & Modules Implemented

---

## 1. Executive Summary & Mission

**AeroCool-AI** is a Physics-Informed Machine Learning (PINN) and geospatial analytics platform engineered to:
1. **Detect Urban Heat Island (UHI) Hotspots:** Ingest high-resolution thermal and multispectral Earth observation data to identify spatial heat anomalies and quantify dominant microclimate drivers (albedo, vegetation deficit, building height/density, street canyon trapping).
2. **Model Microclimate Thermodynamics with Physics Constraints:** Enforce the **Surface Energy Balance (SEB)** conservation law ($R_n - G - H - \lambda E = 0$) and 2D advection-diffusion thermal PDEs inside neural network loss functions, preventing unphysical temperature predictions.
3. **Simulate & Optimize Spatial Cooling Interventions:** Provide municipal planners with parametric simulation and constrained mathematical optimization solvers to allocate green roofs, high-albedo cool roofs, urban tree canopies, and permeable pavements under budget and social vulnerability constraints.

---

## 2. Core Technology Stack

| Domain | Technology / Tool | Version / Purpose |
|---|---|---|
| **Language & Runtime** | Python | `>=3.14` (specified in `.python-version`) |
| **Package & Env Manager** | `uv` (Astral) | Ultra-fast dependency resolution and lockfile management (`pyproject.toml`, `uv.lock`) |
| **Web API Framework** | FastAPI + Uvicorn | High-performance ASGI framework with Pydantic v2 validation |
| **Physics-Informed ML** | PyTorch | Neural network modeling with Random Fourier Features and Autograd spatial/temporal differential operators |
| **Empirical ML Benchmark**| XGBoost / Scikit-learn | Tree-based empirical regression and feature importance gains |
| **Geospatial & Remote Sensing**| GeoPandas, Rasterio, Shapely, OSMnx, Earth Engine API | Raster/vector processing, coordinate transformations, and Overpass vector queries |
| **Spatial Database** | PostgreSQL 16 + PostGIS 3.4 | Relational spatial persistence with GeoAlchemy2 and SQLAlchemy 2.0 (asyncpg) |
| **Caching & Message Broker**| Redis 7 | High-speed response caching with in-memory fallback |
| **Containerization** | Docker & Docker Compose | Multi-container composition (`postgis`, `redis`, `api`) |
| **Testing** | Pytest + Pytest-Asyncio + HTTPX | Asynchronous unit and integration test suite |

---

## 3. Current Project Status & Implemented Modules

All core modules are fully structured under the `src/` layout following the **Single-Responsibility Principle (SRP)**.

### Subsystem Completion Matrix

| Subsystem | Submodule | Status | Implementation Details |
|---|---|---|---|
| **Configuration** | `aerocool_ai.config` | **Complete** | Pydantic `BaseSettings` class ([`Settings`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/config.py)), DSN property builders, cached singleton provider. |
| **Data Ingestion** | `core_engine.ingestion` | **Complete** | Ingestion collectors for Landsat 8/9 LST (GEE), ECOSTRESS diurnal LST, Sentinel-2 L2A & LULC, ERA5-Land meteo forcings, and OSM 3D morphology. |
| **Preprocessing** | `core_engine.preprocessing` | **Complete** | Reprojection & grid matching, MinMax/Z-score/Robust scaling, EDT NoData inpainting, and biophysical indices ($\text{NDVI}, \text{NDBI}, \text{NDWI}, \text{Albedo}, \text{FVC}, \varepsilon, \text{SVF}$). |
| **Physics & ML** | `core_engine.models` | **Complete** | [`UrbanHeatPINN`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/models/pinn_heat_dynamics.py) with hardware auto-detection (CUDA/MPS/CPU) & accelerated inference, [`SurfaceEnergyBalanceLoss`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/models/loss_functions.py), [`PINNTrainingPipeline`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/models/train_pipeline.py), and [`LSTBaselineRegressor`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/models/baseline_regressor.py). |
| **Optimization** | `core_engine.optimization` | **Complete** | [`CoolingInterventionSimulator`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/optimization/cooling_simulator.py), Mixed-Integer Linear Programming (MILP) & greedy [`SpatialAllocationSolver`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/optimization/spatial_allocator.py), Pareto frontier generator, and [`ImpactEvaluator`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/optimization/impact_evaluator.py). |
| **Frontend Subsystem** | `aerocool_ai.frontend` | **Complete** | High-performance **React 19 + TypeScript + Vite + Tailwind CSS + Leaflet** SPA with code-splitting, A/B policy comparison, Pareto curves, Indian city presets, and printable Heat Action Plans. |
| **Persistence** | `database` | **Complete** | Async SQLAlchemy 2.0 connection pool ([`connection.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/connection.py)), GeoAlchemy2 models ([`spatial_layers.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/spatial_layers.py), [`scenario_results.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/scenario_results.py), [`sensor_meteo.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/sensor_meteo.py)), and async spatial repositories. |
| **Backend API** | `backend_api` | **Complete** | FastAPI application ([`main.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/main.py)), dependency injection, Pydantic v2 schemas, and endpoints for `/hotspots`, `/simulation`, and `/optimization`. |
| **Provisioning** | `misc_scripts` | **Complete** | [`initialize_postgis.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/misc_scripts/initialize_postgis.py) standalone script for PostGIS extension creation and ORM table creation. |
| **Test Suite** | `tests/` | **Complete** | Comprehensive unit & async integration tests across config, ingestion, preprocessing, PINN models, optimization solvers, and FastAPI routes. |

---

## 4. Scientific Formulations & Physics Equations

When modifying or extending the physics and optimization modules, you **must adhere to these physical laws**:

### 4.1. Surface Energy Balance (SEB) Conservation
$$\mathcal{R}_{\text{SEB}} = R_n - G - H - \lambda E = 0$$

1. **Stefan-Boltzmann Net Radiation ($R_n$)**:
   $$R_n = (1 - \alpha) R_{sw\downarrow} + \varepsilon R_{lw\downarrow} - \varepsilon \sigma (T_s + 273.15)^4$$
   - $\sigma = 5.670374 \times 10^{-8} \, \text{W}/(\text{m}^2 \text{K}^4)$
   - $\alpha$: Liang (2001) broadband shortwave albedo:
     $$\alpha = 0.356 B_2 + 0.130 B_4 + 0.373 B_8 + 0.085 B_{11} + 0.072 B_{12} - 0.0018$$
   - $\varepsilon$: Sobrino et al. thermal emissivity from Fractional Vegetation Cover ($\text{FVC}$).
2. **Sensible Turbulent Heat Flux ($H$)**:
   $$H = \rho_{\text{air}} c_p \frac{T_s - T_{\text{air}}}{r_a}, \quad r_a = \frac{\ln(z / z_0)^2}{\kappa^2 u_{10}}$$
   - $\rho = 1.205 \, \text{kg/m}^3, c_p = 1005 \, \text{J}/(\text{kg}\cdot\text{K}), \kappa = 0.40$ (Von Kármán constant).
   - $z_0$: Aerodynamic roughness length derived from building height and plan area fraction: $z_0 = 0.10 H_{\text{mean}} \sqrt{\lambda_p}$.
3. **Latent Heat Flux ($\lambda E$)**:
   $$\lambda E \ge 0, \quad \lambda E = f_v \cdot \text{ET}_0(R_n, T_{\text{air}}, u_{10}, \text{RH})$$
4. **Ground / Canopy Structural Heat Storage ($G$)**:
   $$G = \mu R_n \quad (\mu \in [0.15, 0.40] \text{ for high-density urban fabric})$$

### 4.2. Transient 2D Advection-Diffusion PDE
$$\mathcal{R}_{\text{PDE}} = \frac{\partial T_s}{\partial t} - D \left( \frac{\partial^2 T_s}{\partial x^2} + \frac{\partial^2 T_s}{\partial y^2} \right) + \mathbf{u} \cdot \nabla T_s - \frac{R_n - G - H - \lambda E}{\rho C_{\text{eff}}} = 0$$

- Evaluated in [`loss_functions.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/models/loss_functions.py) using PyTorch autograd derivatives ($\frac{\partial T_s}{\partial t}, \nabla^2 T_s$) from [`pinn_heat_dynamics.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/models/pinn_heat_dynamics.py).

### 4.3. Parametric Cooling Intervention Thermodynamics
$$\Delta T_{\text{total}} = \frac{R_{sw} \cdot \Delta \alpha}{h_c} + \frac{\Delta f_v \cdot \lambda \text{ET}}{h_c} + \frac{\text{Shade} \cdot R_{sw}}{1.5 h_c}$$
($h_c \approx 25\,\text{W}/(\text{m}^2 \text{K})$ convective transfer coefficient).

---

## 5. Architectural Directory Layout & File References

```text
AeroCool-AI/
├── pyproject.toml                         # Dependency definitions and scripts
├── uv.lock                                # Pinned package lockfile
├── .python-version                        # Python version (3.14)
├── .gitignore                             # Ignored build, pycache, venv artifacts
├── .env.example                           # Environment configuration template
├── README.md                              # Root user-facing documentation
├── Dockerfile                             # Container deployment image definition
├── docker-compose.yml                     # PostGIS, Redis & API composition
├── AGENTS.md                              # AI Agent Context & Knowledge Base (this file)
│
├── src/aerocool_ai/
│   ├── __init__.py                        # CLI entrypoint (main())
│   ├── config.py                          # Settings (Pydantic BaseSettings)
│   │
│   ├── core_engine/                       # AI/ML & Remote Sensing Subsystem
│   │   ├── ingestion/
│   │   │   ├── gee_landsat_collector.py   # Landsat 8/9 LST ingestion via Earth Engine
│   │   │   ├── ecostress_collector.py     # NASA ECOSTRESS diurnal LST
│   │   │   ├── sentinel_lulc_collector.py # Sentinel-2 multispectral & LULC classes
│   │   │   ├── era5_meteo_collector.py    # ERA5 atmospheric boundary forcings
│   │   │   └── osm_morphology_collector.py# OSM building heights & plan area fraction
│   │   ├── preprocessing/
│   │   │   ├── spatial_alignment.py       # Reprojection, clipping & grid matching
│   │   │   ├── raster_normalizer.py       # Scaling & EDT NoData inpainting
│   │   │   └── feature_extractor.py       # NDVI, NDBI, Albedo, FVC, Emissivity, SVF
│   │   ├── models/
│   │   │   ├── baseline_regressor.py      # XGBoost / Random Forest baseline
│   │   │   ├── pinn_heat_dynamics.py      # PyTorch Fourier-MLP PINN
│   │   │   ├── loss_functions.py          # Surface Energy Balance & PDE loss
│   │   │   └── train_pipeline.py          # Training loop, scheduler & checkpoints
│   │   └── optimization/
│   │       ├── cooling_simulator.py       # Parametric thermodynamic simulator
│   │       ├── spatial_allocator.py       # Constrained spatial allocation solver
│   │       └── impact_evaluator.py        # Thermal comfort, kWh & CO2 impact
│   │
│   ├── frontend/                          # React 19 / TypeScript SPA & Streamlit GUI
│   │   ├── package.json                   # NPM dependencies & scripts
│   │   ├── vite.config.ts                 # Vite bundler & API proxy
│   │   ├── tsconfig.json                  # TypeScript configuration
│   │   ├── tailwind.config.js             # Tailwind CSS theme
│   │   ├── index.html                     # HTML5 entrypoint
│   │   ├── src/                           # React components, services & types
│   │   ├── dist/                          # Compiled production React bundle
│   │   ├── app.py                         # Interactive Streamlit Folium UI
│   │   └── README.md
│   │
│   ├── database/                          # PostGIS Persistence Subsystem
│   │   ├── connection.py                  # Async SQLAlchemy 2.0 engine & sessionmaker
│   │   ├── models/
│   │   │   ├── spatial_layers.py          # SpatialRasterLayer & SpatialVectorFeature
│   │   │   ├── scenario_results.py        # SimulationScenario & ScenarioResultRecord
│   │   │   └── sensor_meteo.py            # MeteoObservation (in-situ sensor logs)
│   │   └── repositories/
│   │       ├── layer_repository.py        # PostGIS ST_Intersects layer queries
│   │       └── scenario_repository.py     # Scenario tracking & result logging
│   │
│   ├── backend_api/                       # FastAPI Web Subsystem
│   │   ├── main.py                        # ASGI app & lifespan manager
│   │   ├── dependencies.py                # DB, Redis & Settings dependencies
│   │   ├── schemas/                       # Pydantic v2 schemas
│   │   │   ├── hotspot_schema.py          # GeoJSON UHI hotspot representations
│   │   │   ├── scenario_request.py        # Simulation request/response payloads
│   │   │   └── optimization_response.py   # Spatial placement & Pareto responses
│   │   └── routes/                        # Route controllers
│   │       ├── hotspots.py                # POST /detect, GET /{hotspot_id}
│   │       ├── simulation.py              # POST /run, GET /{scenario_id}, GET /
│   │       └── optimization.py            # POST /allocate, POST /pareto
│   │
│   └── misc_scripts/                      # Utilities & Migrations
│       └── initialize_postgis.py          # PostGIS extension & table initialization
│
└── tests/                                 # Pytest Verification Suite
    ├── conftest.py                        # Async HTTP test client fixtures
    ├── test_config.py                     # Configuration validation tests
    ├── test_ingestion.py                  # Remote sensing ingestion tests
    ├── test_preprocessing.py              # Spatial alignment & indices tests
    ├── test_models.py                     # PINN autograd, SEB loss & ML regressor tests
    ├── test_optimization.py              # Simulator, allocator & evaluator tests
    └── test_api.py                        # FastAPI integration tests
```

---

## 6. Guidelines & Rules for Future AI Agents

When interacting with, modifying, or extending this codebase, **always adhere strictly to the following standards**:

### 6.1. Package Management & Tooling
- **Always use `uv`**:
  - Add packages: `uv add <package>` (or `uv add --dev <package>`).
  - Sync environment: `uv sync`.
  - Run commands/tests: `uv run pytest`, `uv run uvicorn ...`, `uv run streamlit ...`.
  - **Never** use raw `pip install` without uv context.

### 6.2. Imports & Namespace
- **Always use absolute imports** starting from `aerocool_ai.<submodule>`:
  ```python
  # Good
  from aerocool_ai.config import get_settings
  from aerocool_ai.core_engine.models import UrbanHeatPINN

  # Bad
  from ..config import get_settings
  ```

### 6.3. Single Responsibility Principle (SRP)
- **Ingestion modules** must only fetch, calibrate, and return structured dataclasses (`LSTRasterResult`, `ERA5MeteoGrid`, etc.).
- **Preprocessing modules** must only perform transformations, scalings, and biophysical index calculations.
- **Model modules** must never touch raw HTTP requests or database ORM sessions.
- **Repositories** must encapsulate all raw SQLAlchemy / PostGIS queries.
- **Route controllers** must delegate heavy processing to core engine classes and repositories.

### 6.4. Graceful Fallbacks & Offline Capability
- The ingestion collectors (`gee_landsat_collector.py`, `osm_morphology_collector.py`, etc.) implement high-fidelity synthetic fallbacks when external APIs (Earth Engine credentials, Overpass network) are unavailable.
- Maintain this pattern: **all automated tests and local development must function completely offline without blocking on external API tokens**.

### 6.5. Type Annotations & Documentation
- Maintain 100% type hint coverage (`typing`, Pydantic models, NumPy/PyTorch tensor types).
- Maintain comprehensive Google/Sphinx style docstrings on all public methods.
- If creating new folders or submodules, **always create a corresponding `README.md`** describing the new module.

---

## 7. Useful Agent Quick-Commands

```bash
# 1. Synchronize dependencies
uv sync

# 2. Run the complete test suite
uv run pytest -v

# 3. Run a specific test module
uv run pytest tests/test_models.py -v

# 4. Start PostGIS and Redis (Docker)
docker-compose up -d postgis redis

# 5. Provision PostGIS extensions and ORM tables
uv run python -m aerocool_ai.misc_scripts.initialize_postgis

# 6. Launch the FastAPI Development Server (serves API and React SPA on :8000/dashboard)
uv run uvicorn aerocool_ai.backend_api.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Launch the React 19 Development Server (Port 3000)
cd src/aerocool_ai/frontend && npm.cmd run dev

# 8. Launch the Streamlit Geospatial Frontend Dashboard (Port 8501)
uv run streamlit run src/aerocool_ai/frontend/app.py --server.port 8501
```
