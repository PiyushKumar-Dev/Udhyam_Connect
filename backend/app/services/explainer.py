from __future__ import annotations


def _band(score: float) -> str:
    if score >= 0.9:
        return "high"
    if score >= 0.75:
        return "moderate"
    return "low"


def _pct(score: float) -> int:
    return int(round(score * 100))


def generate_explanation(evidence: dict) -> str:
    parts = [
        f"name similarity {_pct(evidence['name_score'])}% ({_band(evidence['name_score'])})",
        f"address similarity {_pct(evidence['address_score'])}% ({_band(evidence['address_score'])})",
    ]

    if evidence.get("shared_pan"):
        parts.append(f"shared PAN {evidence['shared_pan']} (exact)")
    else:
        parts.append(f"PAN comparison {_pct(evidence['pan_score'])}%")

    if evidence.get("shared_gstin"):
        parts.append(f"shared GSTIN {evidence['shared_gstin']} (exact)")
    else:
        parts.append(f"GSTIN comparison {_pct(evidence['gstin_score'])}%")

    if evidence.get("licenses_compared"):
        parts.append(f"license overlap {_pct(evidence['license_score'])}%")
    else:
        parts.append("license data not available for comparison")

    return f"Matched because: {', '.join(parts)}. Final confidence {_pct(evidence['final'])}%."
