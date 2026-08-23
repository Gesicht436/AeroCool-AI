"""SQLAlchemy 2.0 Async Connection and Sessionmaker Management.

Configures asynchronous PostgreSQL connection pools with PostGIS support via asyncpg.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from aerocool_ai.config import Settings, get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base declarative class for all PostGIS and application tables."""

    pass


_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine(settings: Optional[Settings] = None) -> AsyncEngine:
    """Provide or instantiate singleton async SQLAlchemy database engine."""
    global _engine
    if _engine is None:
        cfg = settings or get_settings()
        db_url = cfg.async_database_url
        logger.info(f"Creating async database engine for: {db_url.split('@')[-1]}")
        _engine = create_async_engine(
            db_url,
            echo=cfg.debug,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def get_session_factory(
    settings: Optional[Settings] = None,
) -> async_sessionmaker[AsyncSession]:
    """Provide or instantiate async sessionmaker."""
    global _sessionmaker
    if _sessionmaker is None:
        engine = get_engine(settings)
        _sessionmaker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator providing transactional async DB sessions."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection() -> None:
    """Gracefully terminate database connection pools on shutdown."""
    global _engine, _sessionmaker
    if _engine is not None:
        logger.info("Disposing async database connection pool.")
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
