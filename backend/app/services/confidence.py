from __future__ import annotations

from typing import Any
from backend.app.utils.ml_client import ml_client

AUTO_LINK_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.50

def compute_match_evidence(record_a: Any, record_b: Any) -> dict[str, Any]:
    # Convert records to dicts for ML service
    dict_a = {
        "norm_name": record_a.norm_name,
        "norm_address": record_a.norm_address,
        "pan": record_a.pan,
        "gstin": record_a.gstin
    }
    dict_b = {
        "norm_name": record_b.norm_name,
        "norm_address": record_b.norm_address,
        "pan": record_b.pan,
        "gstin": record_b.gstin
    }
    
    # Call ML Service
    ml_result = ml_client.compute_match(dict_a, dict_b)
    
    # Format result to match expected schema in backend
    evidence = ml_result.get("evidence", {})
    return {
        "name_score": evidence.get("name_score", 0.0),
        "address_score": evidence.get("address_score", 0.0),
        "pan_score": evidence.get("pan_score", 0.0),
        "gstin_score": evidence.get("gstin_score", 0.0),
        "license_score": 0.0, # Handled by ML service or simplified for now
        "final": ml_result.get("confidence", 0.0),
        "threshold_used": "AUTO_LINK" if ml_result.get("decision") == "AUTO_LINKED" else "REVIEW" if ml_result.get("decision") == "PENDING" else "SEPARATE",
        "justification": ml_result.get("justification", ""),
        "shared_pan": record_a.pan if record_a.pan and record_a.pan == record_b.pan else None,
        "shared_gstin": record_a.gstin if record_a.gstin and record_a.gstin == record_b.gstin else None,
    }
