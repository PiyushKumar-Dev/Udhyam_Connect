from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base, JSON_TYPE, UUID_TYPE

if TYPE_CHECKING:
    from backend.app.models.entity import SourceRecord
    from backend.app.models.review import ReviewTask


@dataclass(slots=True)
class MatchEvidence:
    name_score: float
    address_score: float
    pan_score: float
    gstin_score: float
    license_score: float
    final: float
    threshold_used: str


class MatchPair(Base):
    __tablename__ = "match_pairs"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    record_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("source_records.id"), nullable=False
    )
    record_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("source_records.id"), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    evidence: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    record_a: Mapped[SourceRecord] = relationship(
        "SourceRecord", foreign_keys=[record_a_id], back_populates="record_a_matches"
    )
    record_b: Mapped[SourceRecord] = relationship(
        "SourceRecord", foreign_keys=[record_b_id], back_populates="record_b_matches"
    )
    review_tasks: Mapped[list[ReviewTask]] = relationship("ReviewTask", back_populates="match_pair")
