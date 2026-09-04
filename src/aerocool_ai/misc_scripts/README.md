# Database Provisioning & Administrative Utilities (`src/aerocool_ai/misc_scripts/`)

This directory contains administrative and migration scripts for database initialization, PostGIS spatial extension enablement, and table schema provisioning.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/misc_scripts/__init__.py)
- **Role**: Exports administrative utilities.
- **Exports**: `init_database`.

---

### 2. [`initialize_postgis.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/misc_scripts/initialize_postgis.py)
- **Role**: Standalone async script that connects to the PostgreSQL database, creates the required PostGIS spatial extensions, and builds all ORM tables.
- **Key Operations**:
  1. Establishes an async database connection using `get_engine()`.
  2. Executes raw SQL:
     ```sql
     CREATE EXTENSION IF NOT EXISTS postgis;
     CREATE EXTENSION IF NOT EXISTS postgis_topology;
     ```
  3. Invokes `Base.metadata.create_all` to provision all application tables:
     - `spatial_raster_layers`
     - `spatial_vector_features`
     - `simulation_scenarios`
     - `scenario_results`
     - `meteo_observations`
     - `users`
     - `telemetry_events`
  4. Automatically seeds the database with default demo accounts:
     - **Administrator**: `admin@aerocool.ai` (Password: `Admin@123`, Role: `admin`)
     - **Climate Planner**: `planner@aerocool.ai` (Password: `Planner@123`, Role: `customer`)
- **Usage**:
  ```bash
  # Execute via uv runner
  uv run python -m aerocool_ai.misc_scripts.initialize_postgis
  ```
