from __future__ import annotations

import io
import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.auth import require_roles
from backend.app.database import get_db
from backend.app.schemas.ingest import IngestSummaryResponse
from backend.app.services.entity_resolution import ingest_records, normalise_source_system

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


def _infer_source_system(filename: str) -> str:
    lower = filename.lower()
    if "gst" in lower:
        return "GST"
    if "mca" in lower:
        return "MCA"
    if "fire" in lower or "noc" in lower:
        return "FIRE"
    if "labour" in lower or "labor" in lower or "shops" in lower:
        return "LABOUR"
    if "pollution" in lower or "consent" in lower:
        return "POLLUTION"
    if "utility" in lower:
        return "UTILITY"
    return "MUNICIPAL"


def _clean_record(row: dict) -> dict:
    cleaned: dict = {}
    for key, value in row.items():
        if pd.isna(value):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned


@router.post("", response_model=IngestSummaryResponse)
async def ingest(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("analyst", "admin")),
) -> IngestSummaryResponse:
    payloads: list[dict] = []

    for upload in files:
        content = await upload.read()
        filename = upload.filename or "upload"
        source_system = _infer_source_system(filename)
        if filename.lower().endswith(".csv"):
            frame = pd.read_csv(io.BytesIO(content))
            for record in frame.to_dict(orient="records"):
                cleaned = _clean_record(record)
                cleaned["source_system"] = normalise_source_system(str(cleaned.get("source_system") or source_system))
                payloads.append(cleaned)
            continue

        if filename.lower().endswith(".json"):
            loaded = json.loads(content.decode("utf-8"))
            records = loaded if isinstance(loaded, list) else loaded.get("items", [])
            for record in records:
                if not isinstance(record, dict):
                    continue
                record["source_system"] = normalise_source_system(str(record.get("source_system") or source_system))
                payloads.append(record)
            continue

        raise HTTPException(status_code=422, detail=f"Unsupported file format for {filename}.")

    return IngestSummaryResponse(**ingest_records(db, payloads))
