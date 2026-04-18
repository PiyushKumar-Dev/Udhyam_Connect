from __future__ import annotations

import io
import json


def test_approve_pending_match_merges_records_and_clears_queue(client) -> None:
    records = [
        {
            "source_uid": "mca-101",
            "source_system": "MCA",
            "business_name": "Northwind Logistics Private Limited",
            "address": "44 River Street, Chennai",
            "license_id": "TRADE-44",
        },
        {
            "source_uid": "municipal-101",
            "source_system": "MUNICIPAL",
            "business_name": "Northwind Logistics Pvt Ltd",
            "address": "44 River Street, Chennai",
            "license_id": "TRADE-44",
        },
    ]

    ingest = client.post(
        "/api/ingest",
        files={"files": ("review_candidates.json", io.BytesIO(json.dumps(records).encode("utf-8")), "application/json")},
    )
    assert ingest.status_code == 200
    assert ingest.json()["sent_to_review"] == 1

    pending = client.get("/api/matches/pending")
    assert pending.status_code == 200
    match = pending.json()[0]

    decision = client.post(
        f"/api/matches/{match['id']}/decide",
        json={"decision": "APPROVE", "reviewer": "qa.reviewer", "note": "Same address and matching trade license."},
    )
    assert decision.status_code == 200
    payload = decision.json()
    assert payload["success"] is True
    assert payload["ubid"].startswith("UBID-")

    queue_after = client.get("/api/matches/pending")
    assert queue_after.status_code == 200
    assert queue_after.json() == []

    entities = client.get("/api/entities")
    assert entities.status_code == 200
    items = entities.json()["items"]
    assert len(items) == 1
    assert items[0]["source_count"] == 2

    detail = client.get(f"/api/entities/{payload['ubid']}")
    assert detail.status_code == 200
    body = detail.json()
    assert len(body["linked_records"]) == 2
    assert body["explanation"]
