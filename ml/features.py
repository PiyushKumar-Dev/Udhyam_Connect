from __future__ import annotations

from typing import Any


def extract_features(evidence: dict[str, Any]) -> dict[str, float]:
    return {
        "name_score": float(evidence.get("name_score", 0.0)),
        "address_score": float(evidence.get("address_score", 0.0)),
        "pan_score": float(evidence.get("pan_score", 0.0)),
        "gstin_score": float(evidence.get("gstin_score", 0.0)),
        "license_score": float(evidence.get("license_score", 0.0)),
        "final": float(evidence.get("final", 0.0)),
    }
