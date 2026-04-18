from __future__ import annotations

import io
import json


def test_graph_overview_and_entity_graph(client) -> None:
    records = [
        {
            "source_uid": "mca-graph-1",
            "source_system": "MCA",
            "business_name": "Harbor Foods Private Limited",
            "address": "21 Lake View Road, Kochi",
            "license_id": "LAKE-21",
        },
        {
            "source_uid": "municipal-graph-1",
            "source_system": "MUNICIPAL",
            "business_name": "Harbor Foods Pvt Ltd",
            "address": "21 Lake View Road, Kochi",
            "license_id": "LAKE-21",
        },
    ]

    ingest = client.post(
        "/api/ingest",
        files={"files": ("graph_records.json", io.BytesIO(json.dumps(records).encode("utf-8")), "application/json")},
    )
    assert ingest.status_code == 200

    overview = client.get("/api/graph/overview")
    assert overview.status_code == 200
    body = overview.json()
    assert body["metrics"]["business_count"] >= 1
    assert body["hotspots"]

    focus_ubid = body["hotspots"][0]["ubid"]
    entity_graph = client.get(f"/api/graph/entity/{focus_ubid}")
    assert entity_graph.status_code == 200
    graph_body = entity_graph.json()
    assert graph_body["focus_ubid"] == focus_ubid
    assert any(node["node_type"] == "business" for node in graph_body["nodes"])
    assert any(node["node_type"] == "record" for node in graph_body["nodes"])
