from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.auth import require_roles
from backend.app.database import get_db
from backend.app.schemas.graph import EntityGraphResponse, GraphOverviewResponse
from backend.app.services.graph_analytics import get_entity_graph, get_graph_overview

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/overview", response_model=GraphOverviewResponse)
def graph_overview(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("viewer", "analyst", "admin")),
) -> GraphOverviewResponse:
    return get_graph_overview(db)


@router.get("/entity/{ubid}", response_model=EntityGraphResponse)
def entity_graph(
    ubid: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("viewer", "analyst", "admin")),
) -> EntityGraphResponse:
    try:
        return get_entity_graph(db, ubid)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
