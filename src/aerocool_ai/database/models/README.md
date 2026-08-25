# PostGIS SQLAlchemy Declarative Models (`src/aerocool_ai/database/models/`)

This directory contains GeoAlchemy2 and SQLAlchemy 2.0 declarative database models representing spatial layers, simulation runs, impact results, in-situ meteorological observations, user authentication accounts, and real-time telemetry events.

---

## Entity Relationship (ER) Diagram

```mermaid
erDiagram
    UserAccount {
        string id PK
        string email UK
        string hashed_password
        string full_name
        string role "admin | customer"
        string organization
        boolean is_active
        datetime created_at
        datetime last_login_at
    }

    TelemetryEvent {
        string id PK
        string endpoint
        string method
        int status_code
        float duration_ms
        string user_id FK
        string user_role
        string ip_address
        string user_agent
        string error_message
        datetime timestamp
    }

    SpatialRasterLayer {
        string id PK
        string layer_name
        string layer_type
        string sensor_source
        float resolution_meters
        string crs
        geometry bounds_geom "POLYGON SRID 4326"
        string storage_uri
        datetime timestamp
        jsonb layer_metadata
        datetime created_at
    }

    SpatialVectorFeature {
        string id PK
        string feature_type
        geometry geometry "GEOMETRY SRID 4326"
        float height_m
        float plan_area_m2
        float albedo
        float fvc
        jsonb properties
        datetime created_at
    }

    SimulationScenario ||--o{ ScenarioResultRecord : "1 to Many (results)"
    SimulationScenario {
        string id PK
        string scenario_name
        string description
        geometry boundary_geom "POLYGON SRID 4326"
        string strategy_type
        float budget_usd
        float target_area_fraction
        string status
        string error_message
        datetime created_at
        datetime updated_at
    }

    ScenarioResultRecord {
        string id PK
        string scenario_id FK
        float mean_lst_reduction_celsius
        float max_lst_reduction_celsius
        float mean_air_temp_reduction_celsius
        float total_area_modified_m2
        float total_spent_usd
        float annual_cooling_energy_saved_kwh
        float annual_co2_avoided_tons
        float payback_period_years
        jsonb result_geojson
        string raster_artifact_path
        jsonb metadata_json
        datetime created_at
    }

    MeteoObservation {
        string id PK
        string station_id
        string station_name
        geometry location_geom "POINT SRID 4326"
        datetime observation_time
        float air_temp_celsius
        float relative_humidity
        float solar_radiation_wm2
        float wind_speed_ms
        float surface_pressure_hpa
        jsonb metadata_json
        datetime created_at
    }
```

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/__init__.py)
- **Role**: Exports ORM model entities: `UserAccount`, `UserRole`, `TelemetryEvent`, `SpatialRasterLayer`, `SpatialVectorFeature`, `SimulationScenario`, `ScenarioResultRecord`, `MeteoObservation`.

---

### 2. [`users.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/users.py)
- **Role**: User authentication accounts and RBAC roles.
- **Models**:
  - `UserRole`: Enum for user permission levels (`ADMIN`, `CUSTOMER`).
  - `UserAccount`: Stores unique email, PBKDF2 hashed password, full name, role, municipal organization, active status flag, and login audit timestamps.

---

### 3. [`telemetry.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/telemetry.py)
- **Role**: API telemetry and request performance event logs.
- **Models**:
  - `TelemetryEvent`: Stores request endpoint, HTTP method, status code, latency in milliseconds, user identity, IP address, user agent, and timestamp.
  - Indexed on `(endpoint, timestamp)` and `timestamp` for fast dashboard analytics.

---

### 4. [`spatial_layers.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/spatial_layers.py)
- **Role**: Spatial raster catalog and vector feature tables.
- **Models**:
  - `SpatialRasterLayer`: Stores raster metadata, bounding polygons (`Geometry('POLYGON', srid=4326)`), resolution, timestamp, and cloud storage URIs.
  - `SpatialVectorFeature`: Stores vector geometries (building footprints, street polygons, land parcels) with biophysical attributes (`height_m`, `albedo`, `fvc`, `plan_area_m2`).

---

### 5. [`scenario_results.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/scenario_results.py)
- **Role**: Simulation configuration and computed impact logs.
- **Models**:
  - `SimulationScenario`: Represents an urban cooling simulation run with user-defined target bounding polygon (`Geometry('POLYGON', srid=4326)`), strategy type, budget, and lifecycle status (`pending`, `running`, `completed`, `failed`).
  - `ScenarioResultRecord`: Stores computed thermodynamic outputs ($\Delta T_{\text{LST}}$, $\Delta T_{\text{air}}$), annual energy savings ($\text{kWh}$), avoided $\text{CO}_2$ emissions, and full RFC 7946 GeoJSON allocations.

---

### 6. [`sensor_meteo.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/sensor_meteo.py)
- **Role**: In-situ weather station logs for PINN model assimilation.
- **Models**:
  - `MeteoObservation`: Stores sensor spatial coordinates (`Geometry('POINT', srid=4326)`), observation time, air temperature, solar flux, wind speed, relative humidity, and barometric pressure.
