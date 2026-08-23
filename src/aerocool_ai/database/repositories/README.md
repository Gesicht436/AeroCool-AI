# PostGIS Repositories (`src/aerocool_ai/database/repositories/`)

The `repositories` directory encapsulates data access, SQL query construction, and PostGIS spatial relationship operations.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/__init__.py)
- **Role**: Exports public repositories.
- **Exports**: `LayerRepository`, `ScenarioRepository`.

---

### 2. [`layer_repository.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/layer_repository.py)
- **Role**: Manages CRUD and spatial indexing queries for raster catalogs and vector geometry features.
- **Key Methods**:
  - `create_raster_layer()`: Inserts a raster catalog record with automatic PostGIS bounding polygon generation via `ST_MakeEnvelope`.
  - `get_raster_layer_by_id(layer_id)`: Fetches a single raster asset by UUID.
  - `list_raster_layers(layer_type, bbox, limit, offset)`: Queries raster catalog entries with optional spatial bounding box filtering using `ST_Intersects(bounds_geom, envelope)`.
  - `create_vector_feature(feature_type, wkt_geometry, ...)`: Inserts a vector geometry from WKT using `ST_GeomFromText`.
  - `query_vector_features_in_bbox(bbox, feature_type, limit)`: Spatial intersection query returning buildings/parcels within a bounding box.
- **Usage Example**:
  ```python
  from aerocool_ai.database.repositories.layer_repository import LayerRepository

  repo = LayerRepository(session)
  # Find all LST rasters covering downtown Manhattan
  layers = await repo.list_raster_layers(
      layer_type="LST",
      bbox=(-74.02, 40.70, -73.95, 40.78)
  )
  ```

---

### 3. [`scenario_repository.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/scenario_repository.py)
- **Role**: Manages simulation scenario lifecycles, execution status updates, and impact logs.
- **Key Methods**:
  - `create_scenario(scenario_name, strategy_type, budget_usd, boundary_bbox)`: Creates a scenario in `pending` state.
  - `get_scenario_by_id(scenario_id, load_results)`: Retrieves a scenario with optional eager loading of results via `selectinload(SimulationScenario.results)`.
  - `list_scenarios(status, limit, offset)`: Lists historical scenarios with pagination and status filters.
  - `update_scenario_status(scenario_id, status, error_message)`: Updates scenario state (`running`, `completed`, `failed`).
  - `record_scenario_result(scenario_id, mean_lst_reduction, ...)`: Persists computed thermodynamic outputs, energy metrics, and GeoJSON allocations.
- **Usage Example**:
  ```python
  from aerocool_ai.database.repositories.scenario_repository import ScenarioRepository

  repo = ScenarioRepository(session)
  scenario = await repo.create_scenario(
      scenario_name="Midtown Cool Roof Initiative",
      strategy_type="cool_roof",
      budget_usd=300_000.0,
      boundary_bbox=(-74.02, 40.70, -73.95, 40.78),
  )
  ```
