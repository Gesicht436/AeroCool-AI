"""User Account and Role Declarative ORM Models."""

from __future__ import annotations

import datetime
from enum import Enum
import uuid

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from aerocool_ai.database.connection import Base


class UserRole(str, Enum):
    """Supported user role designations."""

    CUSTOMER = "customer"
    ADMIN = "admin"


class UserAccount(Base):
    """User account entity storing credentials, role, and profile attributes."""

    __tablename__ = "user_accounts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), default=UserRole.CUSTOMER.value, nullable=False
    )
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<UserAccount(email='{self.email}', role='{self.role}', active={self.is_active})>"
