from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.risk import RiskSummary


class SourceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_system: str
    raw_name: str
    norm_name: str
    raw_address: str
    norm_address: str
    pan: str | None
    gstin: str | None
    license_ids: list[str]
    raw_payload: dict[str, Any]
    match_confidence: float | None = None


class ActivityEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    event_date: date
    source: str
    payload: dict[str, Any]
    summary: str


class EntitySummary(BaseModel):
    ubid: str
    canonical_name: str
    status: str
    confidence: float
    risk: RiskSummary
    source_count: int
    updated_at: datetime


class EntityListResponse(BaseModel):
    total: int
    items: list[EntitySummary]


class EntityDetailResponse(BaseModel):
    ubid: str
    canonical_name: str
    status: str
    status_reason: str
    confidence: float
    risk: RiskSummary
    explanation: str
    linked_records: list[SourceRecordResponse]
    activity_timeline: list[ActivityEventResponse]
    created_at: datetime
    updated_at: datetime
