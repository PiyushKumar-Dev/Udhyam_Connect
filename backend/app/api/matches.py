from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.auth import require_roles
from backend.app.database import get_db
from backend.app.models.match import MatchPair
from backend.app.schemas.entity import SourceRecordResponse
from backend.app.schemas.match import MatchDecisionRequest, MatchDecisionResponse, MatchPairResponse
from backend.app.services.entity_resolution import decide_match
from backend.app.services.explainer import generate_explanation

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/pending", response_model=list[MatchPairResponse])
def pending_matches(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("analyst", "admin")),
) -> list[MatchPairResponse]:
    query = (
        select(MatchPair)
        .options(selectinload(MatchPair.record_a), selectinload(MatchPair.record_b), selectinload(MatchPair.review_tasks))
        .where(MatchPair.decision == "PENDING")
        .order_by(MatchPair.confidence.desc())
    )
    pairs = db.execute(query).scalars().all()
    items: list[MatchPairResponse] = []
    for pair in pairs:
        if not any(task.status == "OPEN" for task in pair.review_tasks):
            continue
        items.append(
            MatchPairResponse(
                id=str(pair.id),
                confidence=pair.confidence,
                decision=pair.decision,
                created_at=pair.created_at,
                evidence=pair.evidence,
                explanation=generate_explanation(pair.evidence),
                record_a=SourceRecordResponse(
                    id=str(pair.record_a.id),
                    source_system=pair.record_a.source_system,
                    raw_name=pair.record_a.raw_name,
                    norm_name=pair.record_a.norm_name,
                    raw_address=pair.record_a.raw_address,
                    norm_address=pair.record_a.norm_address,
                    pan=pair.record_a.pan,
                    gstin=pair.record_a.gstin,
                    license_ids=list(pair.record_a.license_ids or []),
                    raw_payload=pair.record_a.raw_payload,
                    match_confidence=pair.confidence,
                ),
                record_b=SourceRecordResponse(
                    id=str(pair.record_b.id),
                    source_system=pair.record_b.source_system,
                    raw_name=pair.record_b.raw_name,
                    norm_name=pair.record_b.norm_name,
                    raw_address=pair.record_b.raw_address,
                    norm_address=pair.record_b.norm_address,
                    pan=pair.record_b.pan,
                    gstin=pair.record_b.gstin,
                    license_ids=list(pair.record_b.license_ids or []),
                    raw_payload=pair.record_b.raw_payload,
                    match_confidence=pair.confidence,
                ),
            )
        )
    return items


@router.post("/{match_id}/decide", response_model=MatchDecisionResponse)
def decide_pending_match(
    match_id: str,
    payload: MatchDecisionRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("analyst", "admin")),
) -> MatchDecisionResponse:
    try:
        ubid = decide_match(db, match_id, payload.decision, payload.reviewer, payload.note)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return MatchDecisionResponse(success=True, ubid=ubid)
