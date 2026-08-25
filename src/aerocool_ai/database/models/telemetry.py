"""System Telemetry and API Audit Event Declarative ORM Models."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from aerocool_ai.database.connection import Base


class TelemetryEvent(Base):
    """Telemetry record tracking API requests, performance latency, and user actions."""

    __tablename__ = "telemetry_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    endpoint: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        index=True,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_telemetry_timestamp_endpoint", "timestamp", "endpoint"),
    )

    def __repr__(self) -> str:
        return f"<TelemetryEvent(endpoint='{self.endpoint}', status={self.status_code}, duration={self.duration_ms:.2f}ms)>"
