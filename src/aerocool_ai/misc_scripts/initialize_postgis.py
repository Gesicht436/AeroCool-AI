"""Database and PostGIS Extension Initialization Script.

Creates PostGIS spatial extensions, provisions all database schemas,
and populates baseline spatial seed metadata.
"""

from __future__ import annotations

import asyncio
import datetime
import logging

from sqlalchemy import text

from aerocool_ai.config import get_settings
from aerocool_ai.database.connection import Base, close_db_connection, get_engine
from aerocool_ai.database.models import (
    MeteoObservation,
    ScenarioResultRecord,
    SimulationScenario,
    SpatialRasterLayer,
    SpatialVectorFeature,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("init_postgis")


async def init_database() -> None:
    """Initialize database extensions and create all ORM tables."""
    settings = get_settings()
    engine = get_engine(settings)

    logger.info(f"Connecting to database: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

    try:
        async with engine.begin() as conn:
            # 1. Enable PostGIS extension
            logger.info("Enabling PostGIS extension...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology;"))

            # 2. Create tables
            logger.info("Creating application and spatial catalog tables...")
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database schema and PostGIS extensions initialized successfully!")

    except Exception as exc:
        logger.error(f"Database initialization encountered an error: {exc}", exc_info=True)
        raise
    finally:
        await close_db_connection()


def main() -> None:
    """Synchronous entrypoint for CLI execution."""
    asyncio.run(init_database())


if __name__ == "__main__":
    main()
