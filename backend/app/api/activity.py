from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.auth import require_roles
from backend.app.database import get_db
from backend.app.schemas.activity import ActivityClassificationRequest, ClassificationResponse
from backend.app.services.entity_resolution import apply_activity_status, find_business_by_token

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.post("/classify", response_model=ClassificationResponse)
def classify_activity(
    payload: ActivityClassificationRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("analyst", "admin")),
) -> ClassificationResponse:
    business = find_business_by_token(db, payload.ubid)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found.")
    result = apply_activity_status(db, business, "api")
    db.commit()
    return ClassificationResponse(**result)
