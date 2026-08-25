# Source Root Directory (`src/`)

This directory contains the source code for the **AeroCool-AI** package, structured following the modern Python **`src-layout`** pattern recommended by PyPA and Astral's `uv`.

---

## Why the `src-layout`?

The `src-layout` isolates the importable Python package (`aerocool_ai`) from the project root directory. This design:
1. **Prevents accidental imports against raw source code**: Ensures tests and runtime environments import against the installed editable wheel (`pip install -e .` / `uv run`) rather than local directory artifacts.
2. **Standardizes Build Artifacts**: Allows packaging tools (`uv_build`, `setuptools`, `hatch`) to cleanly isolate package data and binaries.
3. **Strict Namespace Enforcement**: Requires all internal and external imports to follow absolute package notation (`aerocool_ai.<module>`).

---

## Directory Structure

```text
src/
└── aerocool_ai/                 # Root package directory
    ├── __init__.py              # Package initialization and CLI entrypoint
    ├── config.py                # Pydantic Settings & environment variables
    ├── core_engine/             # Remote Sensing, Preprocessing, PINN & Optimization
    ├── frontend/                # React 19 + TypeScript SPA (Cooling Studio & Admin Portal)
    ├── database/                # PostGIS persistence, SQLAlchemy models & repos
    ├── backend_api/             # FastAPI application, auth, telemetry, routes & schemas
    └── misc_scripts/            # Database initialization and maintenance utilities
```

---

## Sub-Packages Overview

- **[`aerocool_ai.core_engine`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/README.md)**:
  Contains the AI/ML, Physics-Informed Neural Network (PINN), biophysical feature extraction, remote sensing ingestion (Landsat, ECOSTRESS, Sentinel-2, ERA5, OSM), and spatial cooling optimization solvers.
- **[`aerocool_ai.frontend`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/frontend/README.md)**:
  Production React 19 + TypeScript + Tailwind CSS + Leaflet geospatial web client with A/B policy comparison and Pareto curves.
- **[`aerocool_ai.database`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/database/README.md)**:
  Asynchronous database persistence layer powered by PostgreSQL 16, PostGIS 3.4, SQLAlchemy 2.0 (asyncpg), and GeoAlchemy2.
- **[`aerocool_ai.backend_api`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/README.md)**:
  Production-grade FastAPI ASGI application exposing REST endpoints for UHI hotspot detection, parametric simulation, and spatial optimization.
- **[`aerocool_ai.misc_scripts`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/misc_scripts/README.md)**:
  Administrative and provisioning scripts, such as PostGIS extension creation and ORM table migrations.

---

## Developer Guidelines

1. **Absolute Imports**: Always import modules starting from the root namespace:
   ```python
   # Correct
   from aerocool_ai.core_engine.models import UrbanHeatPINN
   from aerocool_ai.config import get_settings

   # Incorrect
   from ..models import UrbanHeatPINN
   ```

2. **Single Responsibility Principle (SRP)**: Do not cross-pollinate database persistence logic into physics modeling or FastAPI routing into satellite ingestion collectors.

3. **Running the Application**:
   ```bash
   # Option 1: Run Full-Stack (FastAPI + React Dashboard on :8000/dashboard)
   uv run uvicorn aerocool_ai.backend_api.main:app --reload

   # Option 2: Run React 19 Development Server (Port 3000)
   cd src/aerocool_ai/frontend && npm.cmd run dev
   ```
