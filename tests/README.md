# Test Suite (`tests/`)

This directory contains the automated test suite for **AeroCool-AI**, covering configuration, remote sensing ingestion, preprocessing, physics-informed machine learning, spatial optimization, user authentication, RBAC, telemetry middleware, and FastAPI REST endpoints.

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
├── test_auth_and_admin.py   # PBKDF2 auth, JWT bearer tokens, RBAC & telemetry API tests
└── test_api.py              # FastAPI endpoint integration tests
```

---

## Files in this Directory

### 1. [`conftest.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/conftest.py)
- **Role**: Global test configuration and fixtures.
- **Fixtures**:
  - `async_client`: Asynchronous `httpx.AsyncClient` wired to the FastAPI `app` via `ASGITransport` for fast, in-process HTTP endpoint testing without requiring a live network socket.

---

### 2. [`test_auth_and_admin.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_auth_and_admin.py)
- **Role**: Verifies user authentication, PBKDF2 hashing, JWT access tokens, role-based access control (RBAC), and telemetry endpoints.
- **Key Tests**:
  - `test_demo_login_customer`: Verifies 1-click customer/planner login endpoint (`POST /api/v1/auth/demo-login/customer`).
  - `test_demo_login_admin`: Verifies 1-click admin login endpoint (`POST /api/v1/auth/demo-login/admin`).
  - `test_user_registration_and_login_flow`: Tests user creation (`POST /api/v1/auth/register`), subsequent login (`POST /api/v1/auth/login`), and token authentication (`GET /api/v1/auth/me`).
  - `test_admin_rbac_protection`: Validates 403 Forbidden enforcement on customer tokens accessing admin routes, and 200 OK access for admin tokens on `/api/v1/admin/telemetry`, `/telemetry/logs`, and `/health`.

---

### 3. [`test_config.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_config.py)
- **Role**: Validates application settings, default values, dynamic property formatting (DSN strings), and `@lru_cache` singleton stability.

---

### 4. [`test_ingestion.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_ingestion.py)
- **Role**: Verifies remote sensing and urban morphology data acquisition collectors (Landsat, ECOSTRESS, Sentinel-2, ERA5, OSM).

---

### 5. [`test_preprocessing.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_preprocessing.py)
- **Role**: Verifies raster grid alignment, normalization scaling, and biophysical feature extraction (NDVI, NDBI, Albedo, FVC, Emissivity, SVF).

---

### 6. [`test_models.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_models.py)
- **Role**: Tests empirical ML regressors, PyTorch PINN forward passes, autograd gradient operators, and Surface Energy Balance physics loss functions.

---

### 7. [`test_optimization.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_optimization.py)
- **Role**: Tests parametric cooling simulations, spatial knapsack allocation solvers (greedy and MILP), and impact assessment.

---

### 8. [`test_api.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/tests/test_api.py)
- **Role**: Full asynchronous integration tests for FastAPI REST endpoints (`/health`, `/hotspots/detect`, `/simulation/run`, `/optimization/allocate`, `/optimization/pareto`).

---

## Running the Tests

```bash
# Run full test suite via uv
uv run pytest -v

# Run a specific test module
uv run pytest tests/test_auth_and_admin.py -v
```
