# PostGIS Persistence Layer (`src/aerocool_ai/database/`)

The `database` package manages all relational, time-series, and spatial persistence operations using **PostgreSQL 16**, **PostGIS 3.4**, **SQLAlchemy 2.0 (asyncpg)**, and **GeoAlchemy2**.

---

## Architectural Principles

1. **Fully Asynchronous**: All database sessions, queries, and transactions utilize non-blocking async/await semantics via the high-performance `asyncpg` driver.
2. **First-Class Spatial Support**: Geometries are indexed and queried using PostGIS spatial functions (`ST_Intersects`, `ST_MakeEnvelope`, `ST_Within`).
3. **Clean Repository Pattern**: All SQL queries are encapsulated within dedicated repository classes, keeping business and routing logic independent of ORM specifics.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/__init__.py)
- **Role**: Exports public connection helpers and ORM model classes.
- **Exports**: `Base`, `get_engine`, `get_session_factory`, `get_async_session`, `close_db_connection`, `SpatialRasterLayer`, `SpatialVectorFeature`, `SimulationScenario`, `ScenarioResultRecord`, `MeteoObservation`.

---

### 2. [`connection.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/connection.py)
- **Role**: Manages SQLAlchemy 2.0 async engine creation, connection pooling, and session lifecycles.
- **Key Functions & Objects**:
  - `Base`: Declarative base class for all application tables.
  - `get_engine(settings)`: Singleton async engine with connection pooling (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`).
  - `get_session_factory(settings)`: Singleton `async_sessionmaker[AsyncSession]` bound to the async engine.
  - `get_async_session()`: Async generator function yielding transactional database sessions with automatic commit/rollback handling.
  - `close_db_connection()`: Graceful disposal of database connection pools during application shutdown.
- **Usage Example**:
  ```python
  from aerocool_ai.database.connection import get_async_session

  async for session in get_async_session():
      # Use transactional session
      result = await session.execute(...)
  ```

---

## Sub-Packages Breakdown

| Submodule | Description |
|---|---|
| [`models/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/models/README.md) | GeoAlchemy2 declarative table definitions for spatial raster catalogs, vector features, scenario runs, and meteorological logs. |
| [`repositories/`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/repositories/README.md) | Asynchronous query operations for spatial bounding box intersections, layer indexing, and simulation history management. |

---

## Database Migration & Setup

To provision the PostGIS spatial extensions and tables:

```bash
uv run python -m aerocool_ai.misc_scripts.initialize_postgis
```
