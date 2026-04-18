from pydantic import BaseModel


class StatsResponse(BaseModel):
    total_businesses: int
    active: int
    dormant: int
    closed: int
    pending_review: int
    auto_linked_today: int
    high_risk_entities: int
    source_breakdown: dict[str, int]


class PincodeStatsItem(BaseModel):
    pincode: str
    total: int
    active: int
    dormant: int
    closed: int
    high_risk: int


class PincodeStatsResponse(BaseModel):
    pincodes: list[PincodeStatsItem]
    total_pincodes: int
