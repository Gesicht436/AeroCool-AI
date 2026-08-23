"""AeroCool-AI FastAPI ASGI Application Entrypoint.

Provides the REST API interface for UHI hotspot detection, physics-informed
temperature simulation, and constrained urban cooling optimization.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from aerocool_ai.backend_api.routes.hotspots import router as hotspots_router
from aerocool_ai.backend_api.routes.optimization import router as optimization_router
from aerocool_ai.backend_api.routes.simulation import router as simulation_router
from aerocool_ai.config import get_settings
from aerocool_ai.database.connection import close_db_connection, get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger("aerocool_ai")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager initializing resources and connections."""
    settings = get_settings()
    logger.info(f"Starting AeroCool-AI Service in '{settings.env}' mode.")

    # Initialize / verify database connectivity
    try:
        engine = get_engine(settings)
        async with engine.connect() as conn:
            logger.info("Successfully connected to PostgreSQL/PostGIS database.")
    except Exception as exc:
        logger.warning(
            f"Database connectivity warning: {exc}. "
            f"Ensure PostgreSQL/PostGIS is running if persisting scenarios."
        )

    yield

    # Clean shutdown
    logger.info("Shutting down AeroCool-AI Service and terminating connection pools.")
    await close_db_connection()


app = FastAPI(
    title="AeroCool-AI: Physics-Informed Geospatial Urban Cooling Engine",
    description=(
        "A Physics-Informed Machine Learning (PINN) and geospatial analytics backend "
        "to detect Urban Heat Island (UHI) hotspots, quantify thermodynamic heating drivers, "
        "and optimize spatial cooling interventions (green roofs, cool coatings, urban canopies)."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(hotspots_router, prefix="/api/v1")
app.include_router(simulation_router, prefix="/api/v1")
app.include_router(optimization_router, prefix="/api/v1")


from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check if frontend/dist exists in src/aerocool_ai/frontend/dist to mount React SPA
frontend_dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist_path.exists() and (frontend_dist_path / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_path / "assets")), name="assets")

    @app.get("/app", tags=["Frontend"], include_in_schema=False)
    @app.get("/dashboard", tags=["Frontend"], include_in_schema=False)
    async def serve_spa():
        return FileResponse(str(frontend_dist_path / "index.html"))


@app.get(
    "/health",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
)
async def health_check() -> Dict[str, Any]:
    """Perform basic liveness and system health check."""
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "AeroCool-AI",
        "version": "0.1.0",
        "environment": settings.env,
        "debug": settings.debug,
    }


@app.get("/", tags=["System"], status_code=status.HTTP_200_OK, include_in_schema=False)
async def root() -> Dict[str, str]:
    """Root entrypoint linking to Web Dashboard and API docs."""
    return {
        "message": "Welcome to AeroCool-AI Geospatial Microclimate Engine",
        "web_dashboard": "/dashboard",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
    }
