# AeroCool-AI Root Package (`src/aerocool_ai/`)

The `aerocool_ai` package is the core Python namespace for the AeroCool-AI Geospatial Microclimate & Physics-Informed Machine Learning system.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/__init__.py)
- **Role**: Package initialisation file and CLI entrypoint.
- **Responsibilities**:
  - Exposes the package version (`0.1.0`).
  - Provides the `main()` function invoked by the CLI script `aerocool-ai` (configured in `pyproject.toml`).
  - Initializes and launches the `uvicorn` ASGI server hosting `aerocool_ai.backend_api.main:app`.
- **Usage**:
  ```bash
  # Launch via CLI entrypoint
  aerocool-ai
  # Or via Python module
  python -m aerocool_ai
  ```

### 2. [`config.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/config.py)
- **Role**: Centralized configuration management and credentials validation powered by `pydantic-settings`.
- **Key Classes & Functions**:
  - `Settings`: Subclass of `BaseSettings` defining strictly validated environment variables with type hints, defaults, and aliases:
    - **Application**: `AEROCOOL_ENV`, `AEROCOOL_DEBUG`, `AEROCOOL_APP_HOST`, `AEROCOOL_APP_PORT`, `AEROCOOL_API_PREFIX`, `AEROCOOL_SECRET_KEY`.
    - **Database**: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `DATABASE_URL`.
      - `async_database_url` (property): Automatically builds `postgresql+asyncpg://...` connection strings.
      - `sync_database_url` (property): Builds standard `postgresql://...` connection strings for sync migrations.
    - **Cache**: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`, `REDIS_URL`.
      - `effective_redis_url` (property): Formats authentication parameters into connection URLs.
    - **Satellite & Remote Sensing**: `GEE_SERVICE_ACCOUNT`, `GEE_PRIVATE_KEY_FILE`, `GEE_PROJECT_ID`, `EARTHDATA_BEARER_TOKEN`, `CDS_API_KEY`, `OSM_OVERPASS_URL`.
    - **Physics & ML**: `MODEL_DEVICE`, `MODEL_CHECKPOINT_DIR`, `DATA_CACHE_DIR`, `BATCH_SIZE`, `SEB_LOSS_WEIGHT`, `PDE_LOSS_WEIGHT`, `DATA_LOSS_WEIGHT`.
  - `get_settings()`: Cached `@lru_cache` provider returning a singleton instance of `Settings`.
- **Usage**:
  ```python
  from aerocool_ai.config import get_settings

  settings = get_settings()
  print(f"Connecting to PostGIS at {settings.postgres_host}:{settings.postgres_port}")
  print(f"Async DSN: {settings.async_database_url}")
  ```

---

## Sub-Packages Breakdown

| Submodule | Description |
|---|---|
| [`core_engine/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/README.md) | Remote sensing ingestion, biophysical indices, PyTorch PINN model, SEB physics loss, and spatial optimization algorithms. |
| [`frontend/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/frontend/README.md) | React 19 + TypeScript geospatial SPA with Leaflet maps, A/B policy comparison, Pareto curves, and Heat Action Plans. |
| [`database/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/README.md) | PostGIS spatial persistence layer, Async SQLAlchemy 2.0 connection pool, GeoAlchemy2 declarative tables, and repositories. |
| [`backend_api/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/README.md) | FastAPI ASGI web layer, dependency injection providers, Pydantic v2 validation schemas, and REST route controllers. |
| [`misc_scripts/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/misc_scripts/README.md) | Database initialization scripts, PostGIS extension creation, and administrative tools. |

---

## Development Standards

- **Type Annotations**: All functions must be fully typed using Python standard `typing` and Pydantic models.
- **Error Handling**: In Strict Error Mode, explicit exceptions and HTTP 503 errors are returned when database, cache, or satellite providers are unconfigured or offline (no silent fallbacks or hardcoded mocks).
- **Documentation**: All public classes and functions must include Google/Sphinx style docstrings.
