"""AeroCool-AI: Physics-Informed Geospatial Urban Cooling Engine."""

import sys
import uvicorn

from aerocool_ai.config import get_settings


def main() -> None:
    """CLI entrypoint to launch the AeroCool-AI FastAPI server."""
    settings = get_settings()
    print(f"Starting AeroCool-AI server on {settings.app_host}:{settings.app_port}...")
    uvicorn.run(
        "aerocool_ai.backend_api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )


__all__ = ["main", "get_settings"]
