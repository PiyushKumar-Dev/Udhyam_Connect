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
    # Use ML-generated justification if available (AI for Bharat requirement)
    justification = evidence.get("justification")
    if justification:
        return f"AI Insight: {justification} (Confidence: {_pct(evidence.get('final', 0))}%)"

    # Fallback to template-based explanation
    parts = [
        f"name similarity {_pct(evidence.get('name_score', 0))}%",
        f"address similarity {_pct(evidence.get('address_score', 0))}%",
    ]

    if evidence.get("shared_pan"):
        parts.append(f"shared PAN {evidence['shared_pan']}")
    if evidence.get("shared_gstin"):
        parts.append(f"shared GSTIN {evidence['shared_gstin']}")

    return f"Matched because: {', '.join(parts)}. Final confidence {_pct(evidence.get('final', 0))}%."
