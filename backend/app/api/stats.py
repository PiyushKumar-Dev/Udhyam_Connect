from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.auth import require_roles
from backend.app.database import get_db
from backend.app.models.entity import Business, SourceRecord
from backend.app.models.match import MatchPair
from backend.app.models.review import ReviewTask
from backend.app.schemas.stats import PincodeStatsItem, PincodeStatsResponse, StatsResponse
from backend.app.services.risk import compute_business_risk

router = APIRouter(prefix="/api/stats", tags=["stats"])

_PINCODE_RE = re.compile(r"\b(\d{6})\b")


def _extract_pincode(address: str) -> str | None:
    match = _PINCODE_RE.search(address or "")
    return match.group(1) if match else None


@router.get("", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("viewer", "analyst", "admin")),
) -> StatsResponse:
    businesses = db.execute(select(Business).where(Business.source_records.any())).scalars().all()
    active = len([business for business in businesses if business.status == "ACTIVE"])
    dormant = len([business for business in businesses if business.status == "DORMANT"])
    closed = len([business for business in businesses if business.status == "CLOSED"])
    high_risk_entities = len([business for business in businesses if compute_business_risk(db, business).level == "HIGH"])

    pending_review = db.execute(
        select(func.count(ReviewTask.id)).where(ReviewTask.status == "OPEN")
    ).scalar_one()
    auto_linked_today = db.execute(
        select(func.count(MatchPair.id)).where(
            MatchPair.decision == "AUTO_LINKED",
            func.date(MatchPair.created_at) == date.today(),
        )
    ).scalar_one()
    source_counts = db.execute(
        select(SourceRecord.source_system, func.count(SourceRecord.id)).group_by(SourceRecord.source_system)
    ).all()

    return StatsResponse(
        total_businesses=len(businesses),
        active=active,
        dormant=dormant,
        closed=closed,
        pending_review=int(pending_review),
        auto_linked_today=int(auto_linked_today),
        high_risk_entities=high_risk_entities,
        source_breakdown={source: count for source, count in source_counts},
    )


@router.get("/pincodes", response_model=PincodeStatsResponse)
def get_pincode_stats(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("viewer", "analyst", "admin")),
) -> PincodeStatsResponse:
    businesses = (
        db.execute(
            select(Business)
            .options(selectinload(Business.source_records))
            .where(Business.source_records.any())
        )
        .scalars()
        .all()
    )

    # Map business → pincodes from its linked source records
    pincode_businesses: dict[str, list[Business]] = defaultdict(list)
    for business in businesses:
        seen_pincodes: set[str] = set()
        for record in business.source_records:
            if record.ubid != business.ubid:
                continue
            pincode = _extract_pincode(record.raw_address)
            if pincode and pincode not in seen_pincodes:
                seen_pincodes.add(pincode)
                pincode_businesses[pincode].append(business)

    items: list[PincodeStatsItem] = []
    for pincode, biz_list in sorted(pincode_businesses.items()):
        if q and q.strip() not in pincode:
            continue
        active = sum(1 for b in biz_list if b.status == "ACTIVE")
        dormant = sum(1 for b in biz_list if b.status == "DORMANT")
        closed = sum(1 for b in biz_list if b.status == "CLOSED")
        high_risk = sum(1 for b in biz_list if compute_business_risk(db, b).level == "HIGH")
        items.append(
            PincodeStatsItem(
                pincode=pincode,
                total=len(biz_list),
                active=active,
                dormant=dormant,
                closed=closed,
                high_risk=high_risk,
            )
        )

    # Sort by total descending
    items.sort(key=lambda x: -x.total)

    return PincodeStatsResponse(pincodes=items, total_pincodes=len(items))
