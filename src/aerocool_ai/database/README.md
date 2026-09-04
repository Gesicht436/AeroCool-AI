# PostGIS Persistence Layer (`src/aerocool_ai/database/`)

The `database` package manages all relational, time-series, and spatial persistence operations using **PostgreSQL 16**, **PostGIS 3.4**, **SQLAlchemy 2.0 (asyncpg)**, and **GeoAlchemy2**.

---

## 🌟 Quick Primer for Juniors: What is PostGIS?

If you are accustomed to standard relational SQL databases, here is why we use **PostGIS**:

### 1. Spatial Superpowers for SQL
Standard SQL knows about numbers, strings, and dates, but it has no idea what a "polygon", "bounding box", or "distance in meters" is.
**PostGIS** is an extension for PostgreSQL that adds spatial geometries (`Point`, `Polygon`, `MultiPolygon`) and coordinate reference systems (like `EPSG:4326` latitude/longitude).

### 2. Spatial Indexing (R-Trees)
If a city has 500,000 buildings and you want to find the ones inside a neighborhood bounding box, standard SQL would have to inspect all 500,000 rows one-by-one.
PostGIS uses **R-Tree Spatial Indices** (Bounding Box Trees). It can filter through millions of spatial geometries and find the buildings intersecting your target polygon in just **2 to 5 milliseconds** using the `ST_Intersects` operator:
```sql
SELECT id, height_m FROM spatial_vector_features 
WHERE ST_Intersects(geometry, ST_MakeEnvelope(77.10, 28.58, 77.26, 28.72, 4326));
```

---

## Architectural Principles

1. **Fully Asynchronous**: All database sessions, queries, and transactions utilize non-blocking async/await semantics via the high-performance `asyncpg` driver.
2. **First-Class Spatial Support**: Geometries are indexed and queried using PostGIS spatial functions (`ST_Intersects`, `ST_MakeEnvelope`, `ST_Within`).
3. **Clean Repository Pattern**: All SQL queries are encapsulated within dedicated repository classes, keeping business and routing logic independent of ORM specifics.
4. **Strict Persistence & Error Propagation**: Endpoints directly persist to PostGIS and return explicit 503 errors if PostgreSQL is unavailable (no silent fallbacks or hardcoded data).

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/__init__.py)
- **Role**: Exports public connection helpers and ORM model classes.
- **Exports**: `Base`, `get_engine`, `get_session_factory`, `get_async_session`, `close_db_connection`, `UserAccount`, `UserRole`, `TelemetryEvent`, `SpatialRasterLayer`, `SpatialVectorFeature`, `SimulationScenario`, `ScenarioResultRecord`, `MeteoObservation`.

---

### 2. [`connection.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/connection.py)
- **Role**: Manages SQLAlchemy 2.0 async engine creation, connection pooling, and session lifecycles.
- **Key Functions & Objects**:
  - `Base`: Declarative base class for all application tables.
  - `get_engine(settings)`: Singleton async engine with connection pooling (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`).
  - `get_session_factory(settings)`: Singleton `async_sessionmaker[AsyncSession]` bound to the async engine.
  - `get_async_session()`: Async generator function yielding transactional database sessions with automatic commit/rollback handling.
  - `close_db_connection()`: Graceful disposal of database connection pools during application shutdown.

---

## Sub-Packages Breakdown

| Submodule | Description |
|---|---|
| [`models/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/README.md) | GeoAlchemy2 declarative table definitions for user accounts, telemetry events, spatial raster catalogs, vector features, scenario runs, and meteorological logs. |
| [`repositories/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/README.md) | Asynchronous query operations for user authentication, live telemetry streaming, spatial bounding box intersections, and simulation history management. |

---

## Database Migration & Setup

To provision the PostGIS spatial extensions, ORM tables, and seed default demo accounts:

```bash
uv run python -m aerocool_ai.misc_scripts.initialize_postgis
```
