from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ActivityClassificationRequest(BaseModel):
    ubid: str


class ClassificationTimelineItem(BaseModel):
    date: date
    type: str
    source: str
    summary: str


class ClassificationResponse(BaseModel):
    ubid: str
    status: str
    reason: str
    last_event_date: date | None
    event_count: int
    timeline: list[ClassificationTimelineItem]
