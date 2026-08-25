# FastAPI Web Layer (`src/aerocool_ai/backend_api/`)

The `backend_api` package provides the RESTful API interface for **AeroCool-AI**, built on FastAPI, Pydantic v2, PyJWT, and ASGI standards.

---

## Architectural Principles

1. **Declarative Validation**: All HTTP payloads and responses are validated and serialized via Pydantic v2 schemas.
2. **Role-Based Access Control (RBAC)**: Enforces granular permission separation (`customer` vs `admin`) with JWT bearer token verification.
3. **Automated Telemetry Middleware**: Profiles and records all API request latencies, status codes, and user identities.
4. **Dependency Injection**: Scoped database sessions, Redis caching clients, authentication resolvers, and application settings are injected via FastAPI `Depends()`.
5. **OpenAPI & GeoJSON Compliance**: All spatial endpoints produce and consume standard RFC 7946 GeoJSON FeatureCollections.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/__init__.py)
- **Role**: Exports the FastAPI `app` instance.

---

### 2. [`main.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/main.py)
- **Role**: ASGI application entrypoint and lifespan manager.
- **Responsibilities**:
  - `lifespan(app)`: Initializes database connection pools, verifies PostGIS connectivity on startup, and safely terminates connections on shutdown.
  - Mounts **TelemetryMiddleware** for live request profiling and metrics collection.
  - Configures **CORS Middleware** (`allow_origins=["*"]`, `allow_methods=["*"]`).
  - Mounts API versioned routers under `/api/v1`:
    - `/api/v1/auth` (User login, registration & demo access)
    - `/api/v1/admin` (Admin telemetry KPIs, live request logs & user directory)
    - `/api/v1/hotspots` (Hotspot detection)
    - `/api/v1/simulation` (Cooling simulation)
    - `/api/v1/optimization` (Spatial allocation & Pareto)
  - Exposes system endpoints:
    - `GET /health`: Liveness and diagnostic status check.
    - `GET /`: Root endpoint with links to documentation.
    - `GET /dashboard`, `GET /app`: Serves pre-compiled React 19 SPA dashboard.
    - `StaticFiles`: Mounts `/assets` for frontend JavaScript and CSS bundles.

---

### 3. [`auth.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/auth.py)
- **Role**: Password security and JWT token generation.
- **Responsibilities**:
  - `hash_password(password)`: PBKDF2-HMAC-SHA256 password hashing with random salt.
  - `verify_password(plain, hashed)`: Constant-time password verification.
  - `create_access_token(data, expires_delta)`: Encodes signed HS256 JWT tokens.
  - `decode_access_token(token)`: Validates JWT signature and extracts user payload.

---

### 4. [`dependencies.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/dependencies.py)
- **Role**: Dependency injection providers for route handlers.
- **Providers**:
  - `get_app_settings()`: Provides cached `Settings` instance.
  - `get_db()`: Injects an async database session (`AsyncSession`) and manages transaction commit/rollback.
  - `get_redis_client()`: Injects an async Redis client and raises an explicit 503 error if Redis is unreachable.
  - `get_current_user()`: Validates JWT bearer token and extracts authenticated `UserAccount`.
  - `require_admin()`: Restricts endpoint access exclusively to users with `admin` role.

---

## Sub-Packages Breakdown

| Submodule | Description |
|---|---|
| [`middleware/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/middleware/telemetry_middleware.py) | Performance and telemetry middleware capturing duration, status codes, and user roles. |
| [`schemas/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/README.md) | Pydantic v2 schemas for auth, telemetry, GeoJSON hotspots, simulations, and allocations. |
| [`routes/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/routes/README.md) | FastAPI route controllers for `/auth`, `/admin`, `/hotspots`, `/simulation`, and `/optimization`. |

---

## Running the API Server

```bash
uv run uvicorn aerocool_ai.backend_api.main:app --host 0.0.0.0 --port 8000 --reload
```
