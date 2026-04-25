from __future__ import annotations

from datetime import date
import uuid
from backend.app.models.activity import ActivityEvent, ClassificationResult, TimelineItem
from backend.app.utils.ml_client import ml_client

def _format_ubid(value: uuid.UUID) -> str:
    return f"UBID-{str(value).split('-')[0].upper()}"

def _event_summary(event: ActivityEvent) -> str:
    return str(event.payload.get("summary") or f"{event.event_type.title()} recorded from {event.source}.")

def classify(ubid: uuid.UUID, events: list[ActivityEvent]) -> ClassificationResult:
    # 1. Prepare data for ML service
    event_dicts = [
        {
            "event_type": e.event_type,
            "event_date": str(e.event_date),
            "source": e.source,
            "payload": e.payload
        }
        for e in events
    ]
    
    # 2. Call ML Service
    ml_result = ml_client.compute_risk(str(ubid), event_dicts)
    
    # 3. Handle Status (Hackathon logic: Status is derived from ML risk/activity)
    # If ML says HIGH risk and no recent events, maybe it's DORMANT
    # For now, let's keep the existing status logic but enrich it with ML score
    
    # Existing logic for status (heuristic)
    today = date.today()
    sorted_events = sorted(events, key=lambda item: item.event_date, reverse=True)
    last_event_date = sorted_events[0].event_date if sorted_events else None
    
    # (Keeping some heuristic logic as fallback/combined)
    if not sorted_events or (today - sorted_events[0].event_date).days > 365:
        status = "DORMANT"
    elif ml_result.get("level") == "HIGH":
        status = "DORMANT" # High risk often implies inactivity in this context
    else:
        status = "ACTIVE"

    # Enrich reason with ML justification
    ml_score = ml_result.get("score", 0)
    ml_factors = ", ".join(ml_result.get("factors", []))
    reason = f"ML Risk Score: {ml_score}/100. Factors: {ml_factors}."

    timeline = [
        TimelineItem(
            date=event.event_date,
            type=event.event_type,
            source=event.source,
            summary=_event_summary(event),
        )
        for event in sorted_events[:20]
    ]
    
    return ClassificationResult(
        ubid=_format_ubid(ubid),
        status=status,
        reason=reason,
        last_event_date=last_event_date,
        event_count=len(sorted_events),
        timeline=timeline,
    )
