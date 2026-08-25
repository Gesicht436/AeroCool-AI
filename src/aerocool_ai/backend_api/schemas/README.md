# Pydantic API Schemas (`src/aerocool_ai/backend_api/schemas/`)

This directory contains Pydantic v2 data transfer objects (DTOs) and serialization schemas for request validation and response formatting.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/__init__.py)
- **Role**: Exports public request and response schemas.

---

### 2. [`auth_schema.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/auth_schema.py)
- **Role**: Defines authentication, user account, and JWT token schemas.
- **Key Schemas**:
  - `UserLoginRequest`: Email and plaintext password validation.
  - `UserRegisterRequest`: Email, password (min 6 chars), full name, role (`customer` | `admin`), and organization.
  - `TokenResponse`: Bearer access token string, token type, and embedded user profile.
  - `UserProfileResponse`: User UUID, email, full name, role, organization, active status, and timestamp.
  - `UserListResponse`: Paginated array of user profiles and total count.

---

### 3. [`telemetry_schema.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/telemetry_schema.py)
- **Role**: Defines real-time system telemetry and hardware health diagnostic schemas.
- **Key Schemas**:
  - `TelemetryEventItem`: Structure of an individual API request audit log (endpoint, method, status code, duration in ms, caller role, error message, timestamp).
  - `TelemetrySummaryResponse`: Aggregated performance metrics (total requests, avg latency ms, P95 latency ms, error rate %, cache hit ratio %, status breakdown dictionary, route distribution).
  - `SystemHealthResponse`: Hardware diagnostics (PyTorch device accelerator, CPU %, RSS memory MB, PostGIS connection status, and satellite EO provider status dictionary).

---

### 4. [`hotspot_schema.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/hotspot_schema.py)
- **Role**: Defines GeoJSON-compliant structures for Urban Heat Island (UHI) hotspot detection.
- **Key Schemas**:
  - `HotspotDetectionRequest`: Input bounding box `bbox`, date range, target satellite sensor, minimum temperature anomaly threshold (°C), and spatial resolution.
  - `HotspotProperties`: Thermal properties for an individual hotspot cell (LST, UHI intensity anomaly, regional baseline mean, Heat Vulnerability Index, dominant heating driver, albedo, FVC, building density, SVF, severity level).
  - `HotspotFeature` & `HotspotFeatureCollection`: GeoJSON Feature and FeatureCollection.

---

### 5. [`scenario_request.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/scenario_request.py)
- **Role**: Defines simulation payload and response models.
- **Key Schemas**:
  - `SimulationRunRequest`: Scenario name, bounding box `bbox`, strategy type (`green_roof`, `cool_roof`, `urban_canopy`, `cool_pavement`), target conversion fraction, capital budget ($).
  - `SimulationRunResponse`: Computed thermodynamic results ($\Delta T_{\text{LST}}$, $\Delta T_{\text{air}}$), modified area ($\text{m}^2$), capital cost ($), annual electricity saved ($\text{kWh}$), avoided $\text{CO}_2$ emissions (tons), financial payback (years), and UTCI stress category shift.
  - `ScenarioItemResponse`: Summary model for historical scenario listing.

---

### 6. [`optimization_response.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/optimization_response.py)
- **Role**: Defines spatial optimization and Pareto efficiency schemas.
- **Key Schemas**:
  - `OptimizationAllocationRequest`: Target bounding box, investment budget, permitted intervention techniques, and social vulnerability weighting toggle.
  - `AllocatedParcelSchema`: Metadata for a specific parcel selected for cooling intervention.
  - `OptimizationAllocationResponse`: Total spent, remaining budget, allocated parcel lists, strategy breakdown counts, and full GeoJSON allocation map.
  - `ParetoPointSchema` & `ParetoFrontierResponse`: Series of scenario points mapping investment budget steps to temperature reductions.
