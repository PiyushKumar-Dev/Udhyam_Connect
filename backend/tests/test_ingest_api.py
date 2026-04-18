from __future__ import annotations

import io
import json


def test_ingest_skips_duplicate_source_record(client) -> None:
    payload = [
        {
            "source_uid": "gst-001",
            "source_system": "GST",
            "business_name": "Acme Trading LLP",
            "address": "12 Market Road, Pune",
            "pan": "ABCDE1234F",
            "gstin": "27ABCDE1234F1Z5",
        }
    ]

    first = client.post(
        "/api/ingest",
        files={"files": ("sample_gst.json", io.BytesIO(json.dumps(payload).encode("utf-8")), "application/json")},
    )
    assert first.status_code == 200
    assert first.json()["records_ingested"] == 1
    assert first.json()["new_ubids_created"] == 1

    second = client.post(
        "/api/ingest",
        files={"files": ("sample_gst.json", io.BytesIO(json.dumps(payload).encode("utf-8")), "application/json")},
    )
    assert second.status_code == 200
    assert second.json()["records_ingested"] == 0
    assert second.json()["new_ubids_created"] == 0


def test_ingest_creates_pending_review_for_ambiguous_match(client) -> None:
    records = [
        {
            "source_uid": "mca-001",
            "source_system": "MCA",
            "business_name": "Orbit Foods Private Limited",
            "address": "88 Ring Road, Bengaluru",
            "license_id": "LIC-88",
        },
        {
            "source_uid": "municipal-001",
            "source_system": "MUNICIPAL",
            "business_name": "Orbit Foods Pvt Ltd",
            "address": "88 Ring Road, Bengaluru",
            "license_id": "LIC-88",
        },
    ]

    response = client.post(
        "/api/ingest",
        files={"files": ("sample_records.json", io.BytesIO(json.dumps(records).encode("utf-8")), "application/json")},
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["records_ingested"] == 2
    assert summary["sent_to_review"] == 1

    pending = client.get("/api/matches/pending")
    assert pending.status_code == 200
    matches = pending.json()
    assert len(matches) == 1
    assert matches[0]["decision"] == "PENDING"
