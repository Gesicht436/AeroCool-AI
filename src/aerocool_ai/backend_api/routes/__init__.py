"""FastAPI Route Modules."""

from aerocool_ai.backend_api.routes.admin import router as admin_router
from aerocool_ai.backend_api.routes.auth import router as auth_router
from aerocool_ai.backend_api.routes.hotspots import router as hotspots_router
from aerocool_ai.backend_api.routes.optimization import router as optimization_router
from aerocool_ai.backend_api.routes.simulation import router as simulation_router

__all__ = [
    "hotspots_router",
    "simulation_router",
    "optimization_router",
    "auth_router",
    "admin_router",
]
