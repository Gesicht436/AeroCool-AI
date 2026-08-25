# PostGIS Repositories (`src/aerocool_ai/database/repositories/`)

The `repositories` directory encapsulates data access, SQL query construction, PostGIS spatial relationship operations, user account management, and real-time telemetry log streaming.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/__init__.py)
- **Role**: Exports public repositories: `UserRepository`, `TelemetryRepository`, `LayerRepository`, `ScenarioRepository`.

---

### 2. [`user_repository.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/user_repository.py)
- **Role**: Manages user account queries, creation, and authentication lookups directly in PostgreSQL.
- **Key Methods**:
  - `get_by_email(email)`: Fetches user by normalized lower-case email directly from PostgreSQL.
  - `get_by_id(user_id)`: Fetches user by UUID.
  - `create_user(email, hashed_password, full_name, role, organization)`: Persists a new user record.
  - `list_users(limit, offset)`: Retrieves paginated user directory.
  - `update_last_login(user_id)`: Updates timestamp upon successful authentication.

---

### 3. [`telemetry_repository.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/telemetry_repository.py)
- **Role**: Records API request performance metrics and computes percentile analytics in PostgreSQL.
- **Key Methods**:
  - `log_event(endpoint, method, status_code, duration_ms, ...)`: Persists event directly to PostGIS database.
  - `get_aggregate_metrics()`: Calculates total requests, average latency, 95th percentile latency (P95), error rate percentage, and status code counts.
  - `get_recent_events(limit)`: Returns the most recent API events from the database.

---

### 4. [`layer_repository.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/layer_repository.py)
- **Role**: Manages CRUD and spatial indexing queries for raster catalogs and vector geometry features.
- **Key Methods**:
  - `create_raster_layer()`: Inserts a raster catalog record with automatic PostGIS bounding polygon generation via `ST_MakeEnvelope`.
  - `get_raster_layer_by_id(layer_id)`: Fetches a single raster asset by UUID.
  - `list_raster_layers(layer_type, bbox, limit, offset)`: Queries raster catalog entries with optional spatial bounding box filtering using `ST_Intersects(bounds_geom, envelope)`.
  - `create_vector_feature(feature_type, wkt_geometry, ...)`: Inserts a vector geometry from WKT using `ST_GeomFromText`.
  - `query_vector_features_in_bbox(bbox, feature_type, limit)`: Spatial intersection query returning buildings/parcels within a bounding box.

---

### 5. [`scenario_repository.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/scenario_repository.py)
- **Role**: Manages simulation scenario lifecycles, execution status updates, and impact logs.
- **Key Methods**:
  - `create_scenario(scenario_name, strategy_type, budget_usd, boundary_bbox)`: Creates a scenario in `pending` state.
  - `get_scenario_by_id(scenario_id, load_results)`: Retrieves a scenario with optional eager loading of results via `selectinload(SimulationScenario.results)`.
  - `list_scenarios(status, limit, offset)`: Lists historical scenarios with pagination and status filters.
  - `update_scenario_status(scenario_id, status, error_message)`: Updates scenario state (`running`, `completed`, `failed`).
  - `record_scenario_result(scenario_id, mean_lst_reduction, ...)`: Persists computed thermodynamic outputs, energy metrics, and GeoJSON allocations.
