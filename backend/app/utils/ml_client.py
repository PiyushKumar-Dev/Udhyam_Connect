import httpx
import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")

class MLClient:
    def __init__(self):
        # Using sync client for easy integration into existing sync services
        self.timeout = httpx.Timeout(10.0, connect=2.0)

    def compute_match(self, record_a: Dict[str, Any], record_b: Dict[str, Any]) -> Dict[str, Any]:
        """Calls ML service to compute matching score between two records."""
        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(
                    f"{ML_SERVICE_URL}/api/ml/match",
                    json={"record_a": record_a, "record_b": record_b}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to call ML service match: {e}")
                return {
                    "confidence": 0.5,
                    "decision": "PENDING",
                    "justification": "Fallback logic used (ML Service unavailable).",
                    "evidence": {"error": str(e)}
                }

    def compute_risk(self, ubid: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calls ML service to compute risk score based on activity events."""
        with httpx.Client(timeout=self.timeout) as client:
            try:
                formatted_events = [
                    {
                        "event_type": e.get("event_type", ""),
                        "event_date": str(e.get("event_date", "")),
                        "source": e.get("source", ""),
                        "payload": e.get("payload", {})
                    }
                    for e in events
                ]
                response = client.post(
                    f"{ML_SERVICE_URL}/api/ml/risk",
                    json={"ubid": ubid, "events": formatted_events}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to call ML service risk: {e}")
                return {
                    "level": "UNKNOWN",
                    "score": 0,
                    "factors": ["ML Service unavailable"]
                }

# Singleton instance
ml_client = MLClient()
