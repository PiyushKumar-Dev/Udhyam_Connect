from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.auth import require_roles
from backend.app.database import get_db
from backend.app.models.activity import ActivityEvent
from backend.app.models.entity import Business
from backend.app.schemas.entity import (
    ActivityEventResponse,
    EntityDetailResponse,
    EntityListResponse,
    EntitySummary,
    SourceRecordResponse,
)
from backend.app.services.entity_resolution import (
    find_business_by_token,
    format_ubid,
    get_business_explanation,
    get_record_match_confidence,
)
from backend.app.services.risk import compute_business_risk

router = APIRouter(prefix="/api/entities", tags=["entities"])

_PINCODE_RE = re.compile(r"\b(\d{6})\b")


def _business_has_pincode(business: Business, pincode: str) -> bool:
    for record in business.source_records:
        if record.ubid != business.ubid:
            continue
        match = _PINCODE_RE.search(record.raw_address or "")
        if match and match.group(1) == pincode:
            return True
    return False


def _summary_matches_query(business: Business, query: str) -> bool:
    token = query.lower()
    if token in business.canonical_name.lower():
        return True
    if token in (format_ubid(business.ubid) or "").lower():
        return True
    return any(
        token in (record.pan or "").lower() or token in (record.gstin or "").lower()
        for record in business.source_records
        if record.ubid == business.ubid
    )


def _event_response(event: ActivityEvent) -> ActivityEventResponse:
    return ActivityEventResponse(
        id=str(event.id),
        event_type=event.event_type,
        event_date=event.event_date,
        source=event.source,
        payload=event.payload,
        summary=str(event.payload.get("summary") or f"{event.event_type.title()} reported from {event.source}."),
    )


@router.get("", response_model=EntityListResponse)
def list_entities(
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    pincode: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("viewer", "analyst", "admin")),
) -> EntityListResponse:
    businesses = db.execute(
        select(Business)
        .options(selectinload(Business.source_records))
        .where(Business.source_records.any())
        .order_by(Business.updated_at.desc())
    ).scalars().all()

    filtered = []
    for business in businesses:
        if status and business.status != status.upper():
            continue
        if q and not _summary_matches_query(business, q):
            continue
        if pincode and not _business_has_pincode(business, pincode.strip()):
            continue
        
        computed_risk = compute_business_risk(db, business)
        if risk_level and computed_risk.level != risk_level.upper():
            continue
            
        source_count = len([record for record in business.source_records if record.ubid == business.ubid])
        filtered.append(
            EntitySummary(
                ubid=format_ubid(business.ubid) or "",
                canonical_name=business.canonical_name,
                status=business.status,
                confidence=round(business.confidence, 4),
                risk=computed_risk,
                source_count=source_count,
                updated_at=business.updated_at,
            )
        )

    total = len(filtered)
    start = (page - 1) * limit
    return EntityListResponse(total=total, items=filtered[start : start + limit])


@router.get("/{ubid}", response_model=EntityDetailResponse)
def get_entity(
    ubid: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("viewer", "analyst", "admin")),
) -> EntityDetailResponse:
    business = find_business_by_token(db, ubid)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found.")

    business = db.execute(
        select(Business)
        .options(
            selectinload(Business.source_records),
            selectinload(Business.activity_events),
        )
        .where(Business.ubid == business.ubid)
    ).scalar_one()

    linked_records = sorted(
        [record for record in business.source_records if record.ubid == business.ubid],
        key=lambda item: (item.source_system, item.created_at),
    )
    activity_events = sorted(business.activity_events, key=lambda item: item.event_date, reverse=True)

    return EntityDetailResponse(
        ubid=format_ubid(business.ubid) or "",
        canonical_name=business.canonical_name,
        status=business.status,
        status_reason=business.status_reason,
        confidence=round(business.confidence, 4),
        risk=compute_business_risk(db, business),
        explanation=get_business_explanation(db, business),
        linked_records=[
            SourceRecordResponse(
                id=str(record.id),
                source_system=record.source_system,
                raw_name=record.raw_name,
                norm_name=record.norm_name,
                raw_address=record.raw_address,
                norm_address=record.norm_address,
                pan=record.pan,
                gstin=record.gstin,
                license_ids=list(record.license_ids or []),
                raw_payload=record.raw_payload,
                match_confidence=get_record_match_confidence(db, record),
            )
            for record in linked_records
        ],
        activity_timeline=[_event_response(event) for event in activity_events],
        created_at=business.created_at,
        updated_at=business.updated_at,
    )
