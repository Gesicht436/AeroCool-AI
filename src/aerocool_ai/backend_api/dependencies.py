"""FastAPI Dependency Injection Providers.

Manages scoped database sessions, caching clients, and configuration injection.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from aerocool_ai.config import Settings, get_settings
from aerocool_ai.database.connection import get_async_session

logger = logging.getLogger(__name__)


def get_app_settings() -> Settings:
    """Dependency provider for global application settings."""
    return get_settings()


async def get_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for async SQLAlchemy database session."""
    yield session


import time


class SimpleInMemoryCache:
    """In-memory high-speed cache with TTL expiry when Redis is offline."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, Optional[float]]] = {}

    async def get(self, key: str) -> Optional[str]:
        if key not in self._store:
            return None
        val, expiry = self._store[key]
        if expiry is not None and time.time() > expiry:
            del self._store[key]
            return None
        return val

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        expiry = (time.time() + ex) if ex else None
        self._store[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def ping(self) -> bool:
        return True


_redis_client = None


async def get_redis_client(
    settings: Settings = Depends(get_app_settings),
):
    """Dependency provider for async Redis client with fallback."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(
                settings.effective_redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test ping
            await client.ping()
            _redis_client = client
            logger.info("Connected to Redis cache server.")
        except Exception as exc:
            logger.warning(
                f"Redis connection failed ({exc}). Using in-memory fallback cache."
            )
            _redis_client = SimpleInMemoryCache()

    return _redis_client
