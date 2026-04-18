from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.app.schemas.entity import SourceRecordResponse


class MatchDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(APPROVE|REJECT)$")
    reviewer: str
    note: str = ""


class MatchDecisionResponse(BaseModel):
    success: bool
    ubid: str | None


class MatchPairResponse(BaseModel):
    id: str
    confidence: float
    decision: str
    created_at: datetime
    evidence: dict[str, Any]
    explanation: str
    record_a: SourceRecordResponse
    record_b: SourceRecordResponse
