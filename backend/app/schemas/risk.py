from pydantic import BaseModel


class RiskSummary(BaseModel):
    score: int
    level: str
    reasons: list[str]
