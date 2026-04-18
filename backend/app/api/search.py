from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.auth import require_roles
from backend.app.database import get_db
from backend.app.models.entity import Business
from backend.app.schemas.entity import EntitySummary
from backend.app.services.entity_resolution import format_ubid
from backend.app.services.risk import compute_business_risk

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[EntitySummary])
def search_entities(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("viewer", "analyst", "admin")),
) -> list[EntitySummary]:
    token = q.lower()
    businesses = db.execute(
        select(Business).options(selectinload(Business.source_records)).where(Business.source_records.any())
    ).scalars().all()

    matches: list[EntitySummary] = []
    for business in businesses:
        if token in business.canonical_name.lower() or token in (format_ubid(business.ubid) or "").lower() or any(
            token in (record.pan or "").lower() or token in (record.gstin or "").lower()
            for record in business.source_records
            if record.ubid == business.ubid
        ):
            matches.append(
                EntitySummary(
                    ubid=format_ubid(business.ubid) or "",
                    canonical_name=business.canonical_name,
                    status=business.status,
                    confidence=round(business.confidence, 4),
                    risk=compute_business_risk(db, business),
                    source_count=len([record for record in business.source_records if record.ubid == business.ubid]),
                    updated_at=business.updated_at,
                )
            )

    return matches[:10]
