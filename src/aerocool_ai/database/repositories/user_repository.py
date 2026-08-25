"""User Account Database Repository."""

from __future__ import annotations

import datetime
import logging
from typing import List, Optional
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aerocool_ai.database.models.users import UserAccount, UserRole

logger = logging.getLogger(__name__)


class UserRepository:
    """Async repository for UserAccount persistence."""

    def __init__(self, session: AsyncSession) -> None:
        if session is None:
            raise ValueError("AsyncSession is required for UserRepository operations.")
        self.session = session

    async def get_by_email(self, email: str) -> Optional[UserAccount]:
        """Fetch user by normalized email address from PostgreSQL."""
        clean_email = email.strip().lower()
        stmt = select(UserAccount).where(
            func.lower(UserAccount.email) == clean_email
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[UserAccount]:
        """Fetch user by primary UUID string from PostgreSQL."""
        stmt = select(UserAccount).where(UserAccount.id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        role: str = UserRole.CUSTOMER.value,
        organization: Optional[str] = None,
    ) -> UserAccount:
        """Create and persist a new user account into PostgreSQL."""
        user_id = str(uuid.uuid4())
        clean_email = email.strip().lower()
        now = datetime.datetime.now(datetime.timezone.utc)

        user = UserAccount(
            id=user_id,
            email=clean_email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            organization=organization,
            is_active=True,
            created_at=now,
        )

        self.session.add(user)
        await self.session.flush()
        return user

    async def list_users(self, limit: int = 50, offset: int = 0) -> List[UserAccount]:
        """List registered users from PostgreSQL."""
        stmt = (
            select(UserAccount)
            .order_by(UserAccount.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        db_users = res.scalars().all()
        return list(db_users)

    async def update_last_login(self, user_id: str) -> None:
        """Update last login timestamp in PostgreSQL."""
        now = datetime.datetime.now(datetime.timezone.utc)
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = now
            await self.session.flush()
