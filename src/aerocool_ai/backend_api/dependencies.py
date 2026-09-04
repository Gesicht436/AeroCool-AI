"""FastAPI Dependency Injection Providers.

Manages scoped database sessions, caching clients, user authentication, and configuration injection.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aerocool_ai.backend_api.auth import decode_access_token
from aerocool_ai.config import Settings, get_settings
from aerocool_ai.database.connection import get_async_session
from aerocool_ai.database.models.users import UserAccount, UserRole
from aerocool_ai.database.repositories.telemetry_repository import TelemetryRepository
from aerocool_ai.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


def get_app_settings() -> Settings:
    """Dependency provider for global application settings."""
    return get_settings()


async def get_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for async SQLAlchemy database session."""
    yield session


async def get_redis_client(
    settings: Settings = Depends(get_app_settings),
):
    """Dependency provider for async Redis client in strict mode."""
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            settings.effective_redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await client.ping()
        return client
    except Exception as exc:
        logger.error(f"Redis connection failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Redis cache server unreachable ({exc}). "
                f"Please verify Redis is running at {settings.effective_redis_url} or launch via 'docker compose up -d redis'."
            ),
        )


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """Provide UserRepository instance."""
    return UserRepository(db)


async def get_telemetry_repository(
    db: AsyncSession = Depends(get_db),
) -> TelemetryRepository:
    """Provide TelemetryRepository instance."""
    return TelemetryRepository(db)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserAccount:
    """Validate bearer token and resolve current authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed authentication token payload.",
            )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(val_err),
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await user_repo.get_by_id(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error during user lookup: {exc}",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


async def require_admin_user(
    current_user: UserAccount = Depends(get_current_user),
) -> UserAccount:
    """Require authenticated user to have Administrator privileges."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to access this endpoint.",
        )
    return current_user


require_admin = require_admin_user
