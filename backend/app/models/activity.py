from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base, JSON_TYPE, UUID_TYPE

if TYPE_CHECKING:
    from backend.app.models.entity import Business


@dataclass(slots=True)
class TimelineItem:
    date: date
    type: str
    source: str
    summary: str


@dataclass(slots=True)
class ClassificationResult:
    ubid: str
    status: str
    reason: str
    last_event_date: date | None
    event_count: int
    timeline: list[TimelineItem] = field(default_factory=list)


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    ubid: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, ForeignKey("businesses.ubid"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    business: Mapped[Business] = relationship("Business", back_populates="activity_events")
