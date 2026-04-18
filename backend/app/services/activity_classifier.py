from __future__ import annotations

from datetime import date
import uuid

from backend.app.models.activity import ActivityEvent, ClassificationResult, TimelineItem

ACTIVE_EVENT_TYPES = {"RENEWAL", "INSPECTION", "ELECTRICITY"}
CLOSED_EVENT_TYPES = {"CANCELLED", "SURRENDERED"}


def _format_ubid(value: uuid.UUID) -> str:
    return f"UBID-{str(value).split('-')[0].upper()}"


def _event_summary(event: ActivityEvent) -> str:
    return str(event.payload.get("summary") or f"{event.event_type.title()} recorded from {event.source}.")


def classify(ubid, events: list[ActivityEvent]) -> ClassificationResult:
    today = date.today()
    sorted_events = sorted(events, key=lambda item: item.event_date, reverse=True)
    last_event_date = sorted_events[0].event_date if sorted_events else None

    utility_recent = any(
        event.event_type == "ELECTRICITY" and (today - event.event_date).days <= (18 * 30)
        for event in sorted_events
    )
    closed_event = next(
        (
            event
            for event in sorted_events
            if event.event_type in CLOSED_EVENT_TYPES or str(event.payload.get("status", "")).lower() in {"cancelled", "surrendered"}
        ),
        None,
    )
    if closed_event and not utility_recent:
        status = "CLOSED"
        reason = "Closure-like license event was recorded and no utility usage was seen in the last 18 months."
    elif not sorted_events or (today - sorted_events[0].event_date).days > 365:
        status = "DORMANT"
        reason = "No activity was recorded in the last 12 months."
    elif any(
        event.event_type in ACTIVE_EVENT_TYPES and (today - event.event_date).days <= 183
        for event in sorted_events
    ):
        status = "ACTIVE"
        reason = "A recent renewal, inspection, or electricity event indicates ongoing operations."
    else:
        status = "DORMANT"
        reason = "Insufficient data for an active signal, so the business is treated as dormant."

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
