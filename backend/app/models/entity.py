from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base, JSON_TYPE, UUID_TYPE

if TYPE_CHECKING:
    from backend.app.models.activity import ActivityEvent
    from backend.app.models.match import MatchPair


class Business(Base):
    __tablename__ = "businesses"

    ubid: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DORMANT")
    status_reason: Mapped[str] = mapped_column(Text, nullable=False, default="Awaiting activity classification.")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    source_records: Mapped[list[SourceRecord]] = relationship("SourceRecord", back_populates="business")
    activity_events: Mapped[list[ActivityEvent]] = relationship("ActivityEvent", back_populates="business")


class SourceRecord(Base):
    __tablename__ = "source_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_name: Mapped[str] = mapped_column(Text, nullable=False)
    norm_name: Mapped[str] = mapped_column(Text, nullable=False)
    raw_address: Mapped[str] = mapped_column(Text, nullable=False)
    norm_address: Mapped[str] = mapped_column(Text, nullable=False)
    pan: Mapped[str | None] = mapped_column(String(10), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    license_ids: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    raw_payload: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False)
    ubid: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE, ForeignKey("businesses.ubid"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    business: Mapped[Business | None] = relationship("Business", back_populates="source_records")
    record_a_matches: Mapped[list[MatchPair]] = relationship(
        "MatchPair", foreign_keys="MatchPair.record_a_id", back_populates="record_a"
    )
    record_b_matches: Mapped[list[MatchPair]] = relationship(
        "MatchPair", foreign_keys="MatchPair.record_b_id", back_populates="record_b"
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, nullable=False)
    before_state: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    after_state: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
