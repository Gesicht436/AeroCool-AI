# FastAPI Web Layer (`src/aerocool_ai/backend_api/`)

The `backend_api` package provides the RESTful API interface for **AeroCool-AI**, built on FastAPI, Pydantic v2, and ASGI standards.

---

## Architectural Principles

1. **Declarative Validation**: All HTTP payloads and responses are validated and serialized via Pydantic v2 schemas.
2. **Dependency Injection**: Scoped database sessions, Redis caching clients, and application settings are injected via FastAPI `Depends()`.
3. **OpenAPI & GeoJSON Compliance**: All spatial endpoints produce and consume standard RFC 7946 GeoJSON FeatureCollections.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/__init__.py)
- **Role**: Exports the FastAPI `app` instance.

---

### 2. [`main.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/main.py)
- **Role**: ASGI application entrypoint and lifespan manager.
- **Responsibilities**:
  - `lifespan(app)`: Initializes database connection pools, verifies PostGIS connectivity on startup, and safely terminates connections on shutdown.
  - Configures **CORS Middleware** (`allow_origins=["*"]`, `allow_methods=["*"]`).
  - Mounts API versioned routers under `/api/v1`:
    - `/api/v1/hotspots` (Hotspot detection)
    - `/api/v1/simulation` (Cooling simulation)
    - `/api/v1/optimization` (Spatial allocation & Pareto)
  - Exposes system endpoints:
    - `GET /health`: Liveness and diagnostic status check.
    - `GET /`: Root endpoint with links to documentation.
    - `GET /dashboard`, `GET /app`: Serves pre-compiled React 19 SPA dashboard.
    - `StaticFiles`: Mounts `/assets` for frontend JavaScript and CSS bundles.

---

### 3. [`dependencies.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/dependencies.py)
- **Role**: Dependency injection providers for route handlers.
- **Providers**:
  - `get_app_settings()`: Provides cached `Settings` instance.
  - `get_db()`: Injects an async database session (`AsyncSession`) and manages transaction commit/rollback.
  - `get_redis_client()`: Injects an async Redis client with automatic fallback to `SimpleInMemoryCache` if Redis is offline during local testing.

---

## Sub-Packages Breakdown

| Submodule | Description |
|---|---|
| [`schemas/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/README.md) | Pydantic v2 request/response schemas for GeoJSON hotspots, simulation parameters, and spatial allocations. |
| [`routes/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/routes/README.md) | FastAPI route controllers for `/api/v1/hotspots`, `/api/v1/simulation`, and `/api/v1/optimization`. |

---

## Running the API Server

```bash
uv run uvicorn aerocool_ai.backend_api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)
