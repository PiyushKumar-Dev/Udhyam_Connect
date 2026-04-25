from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from rapidfuzz import fuzz

app = FastAPI(title="Udhyam Connect ML Service - AI for Bharat Edition")

class MatchRequest(BaseModel):
    record_a: dict
    record_b: dict

class ActivityEvent(BaseModel):
    event_type: str
    event_date: str
    source: str
    payload: dict

class RiskRequest(BaseModel):
    ubid: str
    events: List[ActivityEvent]

@app.get("/")
def healthcheck():
    return {"status": "ok", "service": "ml-service", "version": "2.0.0-hackathon"}

@app.post("/api/ml/match")
def compute_match_score(req: MatchRequest):
    a = req.record_a
    b = req.record_b
    
    # 1. Name Similarity (Token Sort handles reordering like 'LTD PVT' vs 'PVT LTD')
    name_score = fuzz.token_sort_ratio(a.get("norm_name", ""), b.get("norm_name", "")) / 100
    
    # 2. Address Similarity (Token Set handles subsets/missing parts)
    addr_score = fuzz.token_set_ratio(a.get("norm_address", ""), b.get("norm_address", "")) / 100
    
    # 3. Identifier Matching (PAN/GSTIN are gold standards)
    pan_match = 1.0 if a.get("pan") and a.get("pan") == b.get("pan") else 0.5 if not a.get("pan") or not b.get("pan") else 0.0
    gst_match = 1.0 if a.get("gstin") and a.get("gstin") == b.get("gstin") else 0.5 if not a.get("gstin") or not b.get("gstin") else 0.0
    
    # Weighted Average
    weights = {"name": 0.35, "address": 0.25, "pan": 0.25, "gstin": 0.15}
    final_score = (
        (name_score * weights["name"]) +
        (addr_score * weights["address"]) +
        (pan_match * weights["pan"]) +
        (gst_match * weights["gstin"])
    )
    
    # Generate Justification (AI for Bharat requirement)
    justification = []
    if pan_match == 1.0:
        justification.append("Identical PAN identifier found.")
    if gst_match == 1.0:
        justification.append("Identical GSTIN identifier found.")
    if name_score > 0.9:
        justification.append("Business names are nearly identical.")
    elif name_score > 0.7:
        justification.append("Significant phonetic/token overlap in business names.")
    
    if final_score < 0.6 and (pan_match == 0.0 or gst_match == 0.0):
        decision = "REJECTED"
        justification.append("Conflicting tax identifiers detected.")
    else:
        decision = "AUTO_LINKED" if final_score > 0.85 else "PENDING"

    return {
        "confidence": round(final_score, 4),
        "decision": decision,
        "justification": " ".join(justification) if justification else "Matched based on combined fuzzy similarity.",
        "evidence": {
            "name_score": round(name_score, 4),
            "address_score": round(addr_score, 4),
            "pan_score": round(pan_match, 4),
            "gstin_score": round(gst_match, 4)
        }
    }

@app.post("/api/ml/risk")
def compute_risk(req: RiskRequest):
    # Risk Scoring Logic for AI for Bharat
    # High risk if no activity in > 1 year
    # Low risk if recent electricity/tax events
    
    events = req.events
    if not events:
        return {"level": "MEDIUM", "score": 50, "reason": "No activity history available for analysis."}
    
    score = 70 # Default base score
    
    # Positive signals
    has_recent_electricity = any(e.event_type == "ELECTRICITY" for e in events[:5])
    has_recent_renewal = any(e.event_type == "RENEWAL" for e in events[:5])
    
    if has_recent_electricity:
        score -= 20
    if has_recent_renewal:
        score -= 15
    
    # Negative signals
    if len(events) < 2:
        score += 10
    
    level = "LOW" if score < 40 else "MEDIUM" if score < 70 else "HIGH"
    
    return {
        "level": level,
        "score": max(0, min(100, score)),
        "factors": [
            "Recent utility usage" if has_recent_electricity else "No recent utility usage",
            "Active license renewals" if has_recent_renewal else "Stale license status"
        ]
    }
