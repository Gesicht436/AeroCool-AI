"""Pytest Global Test Fixtures and Async Configuration."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from aerocool_ai.backend_api.dependencies import get_db
from aerocool_ai.backend_api.main import app
from aerocool_ai.database.connection import Base

# In-memory SQLite async engine for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP test client for FastAPI routes."""
    # Test client using ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
