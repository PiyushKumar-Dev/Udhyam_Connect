from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.models.activity import ActivityEvent
from backend.app.models.entity import Business
from backend.app.models.match import MatchPair
from backend.app.models.review import ReviewTask
from backend.app.schemas.risk import RiskSummary


def compute_business_risk(session: Session, business: Business) -> RiskSummary:
    linked_records = [record for record in business.source_records if record.ubid == business.ubid]
    linked_ids = {record.id for record in linked_records}
    source_systems = sorted({record.source_system for record in linked_records})
    open_reviews = session.execute(
        select(ReviewTask)
        .join(MatchPair, MatchPair.id == ReviewTask.match_pair_id)
        .where(
            ReviewTask.status == "OPEN",
            or_(MatchPair.record_a_id.in_(linked_ids), MatchPair.record_b_id.in_(linked_ids)),
        )
    ).scalars().all()
    recent_events = session.execute(
        select(ActivityEvent)
        .where(ActivityEvent.ubid == business.ubid)
        .order_by(ActivityEvent.event_date.desc())
    ).scalars().all()

    score = 10
    reasons: list[str] = []

    if len(source_systems) >= 4:
        score += 18
        reasons.append("Linked across multiple departments.")
    elif len(source_systems) >= 3:
        score += 10
        reasons.append("Linked across several source systems.")

    if len(linked_records) >= 4:
        score += 16
        reasons.append("High linked-record density.")
    elif len(linked_records) >= 3:
        score += 8
        reasons.append("More than two linked records.")

    if open_reviews:
        score += 20 + (len(open_reviews) * 5)
        reasons.append("Open review tasks still need analyst confirmation.")

    if business.status == "CLOSED" and any(event.event_type == "ELECTRICITY" for event in recent_events[:3]):
        score += 25
        reasons.append("Closed entity still shows recent utility activity.")
    elif business.status == "DORMANT" and len(source_systems) >= 4:
        score += 12
        reasons.append("Dormant status conflicts with broad departmental footprint.")

    if any(event.event_type in {"COMPLAINT", "CANCELLED", "SURRENDERED"} for event in recent_events[:5]):
        score += 10
        reasons.append("Adverse activity signals appear in recent history.")

    score = min(score, 100)
    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not reasons:
        reasons.append("No material anomaly signal detected.")

    return RiskSummary(score=score, level=level, reasons=reasons)
