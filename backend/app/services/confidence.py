from __future__ import annotations

from typing import Any

from rapidfuzz import fuzz

WEIGHTS = {
    "name": 0.30,
    "address": 0.25,
    "pan": 0.25,
    "gstin": 0.15,
    "license": 0.05,
}
AUTO_LINK_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.50


def jaccard_similarity(values_a: set[str], values_b: set[str]) -> float:
    if not values_a and not values_b:
        return 0.0
    union = values_a | values_b
    if not union:
        return 0.0
    return len(values_a & values_b) / len(union)


def identifier_score(value_a: str | None, value_b: str | None) -> float:
    if value_a and value_b:
        return 1.0 if value_a == value_b else 0.0
    return 0.5


def compute_match_evidence(record_a: Any, record_b: Any) -> dict[str, Any]:
    name_score = fuzz.token_sort_ratio(record_a.norm_name, record_b.norm_name) / 100
    address_score = fuzz.token_set_ratio(record_a.norm_address, record_b.norm_address) / 100
    pan_score = identifier_score(record_a.pan, record_b.pan)
    gstin_score = identifier_score(record_a.gstin, record_b.gstin)
    licenses_a = {license_id for license_id in (record_a.license_ids or []) if license_id}
    licenses_b = {license_id for license_id in (record_b.license_ids or []) if license_id}
    license_score = jaccard_similarity(licenses_a, licenses_b)

    final_confidence = round(
        (name_score * WEIGHTS["name"])
        + (address_score * WEIGHTS["address"])
        + (pan_score * WEIGHTS["pan"])
        + (gstin_score * WEIGHTS["gstin"])
        + (license_score * WEIGHTS["license"]),
        4,
    )
    if final_confidence >= AUTO_LINK_THRESHOLD:
        threshold_used = "AUTO_LINK"
    elif final_confidence >= REVIEW_THRESHOLD:
        threshold_used = "REVIEW"
    else:
        threshold_used = "SEPARATE"

    return {
        "name_score": round(name_score, 4),
        "address_score": round(address_score, 4),
        "pan_score": round(pan_score, 4),
        "gstin_score": round(gstin_score, 4),
        "license_score": round(license_score, 4),
        "final": final_confidence,
        "threshold_used": threshold_used,
        "shared_pan": record_a.pan if record_a.pan and record_a.pan == record_b.pan else None,
        "shared_gstin": record_a.gstin if record_a.gstin and record_a.gstin == record_b.gstin else None,
        "licenses_compared": sorted(licenses_a | licenses_b),
    }
