"""Database and PostGIS Extension Initialization Script.

Creates PostGIS spatial extensions, provisions all database schemas,
seeds default demo accounts, and populates baseline spatial seed metadata.
"""

from __future__ import annotations

import asyncio
import datetime
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aerocool_ai.backend_api.auth import hash_password
from aerocool_ai.config import get_settings
from aerocool_ai.database.connection import (
    Base,
    close_db_connection,
    get_engine,
    get_session_factory,
)
from aerocool_ai.database.models import (
    MeteoObservation,
    ScenarioResultRecord,
    SimulationScenario,
    SpatialRasterLayer,
    SpatialVectorFeature,
    TelemetryEvent,
    UserAccount,
    UserRole,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("init_postgis")


async def seed_demo_users(session: AsyncSession) -> None:
    """Seed initial administrator and customer demo accounts if they do not exist."""
    from aerocool_ai.database.repositories.user_repository import UserRepository

    repo = UserRepository(session)

    admin_email = "admin@aerocool.ai"
    existing_admin = await repo.get_by_email(admin_email)
    if not existing_admin:
        logger.info(f"Seeding demo administrator account: {admin_email}")
        await repo.create_user(
            email=admin_email,
            hashed_password=hash_password("Admin@123"),
            full_name="System Administrator",
            role=UserRole.ADMIN.value,
            organization="AeroCool Municipal Operations",
        )

    planner_email = "planner@aerocool.ai"
    existing_planner = await repo.get_by_email(planner_email)
    if not existing_planner:
        logger.info(f"Seeding demo customer/planner account: {planner_email}")
        await repo.create_user(
            email=planner_email,
            hashed_password=hash_password("Planner@123"),
            full_name="City Climate Planner",
            role=UserRole.CUSTOMER.value,
            organization="Delhi Urban Climate Cell",
        )


async def init_database() -> None:
    """Initialize database extensions, create all ORM tables, and seed initial accounts."""
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
            logger.info("Creating application, user, telemetry, and spatial catalog tables...")
            await conn.run_sync(Base.metadata.create_all)

        # 3. Seed initial users
        session_maker = get_session_factory(settings)
        async with session_maker() as session:
            async with session.begin():
                await seed_demo_users(session)

        logger.info("Database schema, PostGIS extensions, and demo accounts initialized successfully!")

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
