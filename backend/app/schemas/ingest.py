from pydantic import BaseModel


class IngestSummaryResponse(BaseModel):
    records_ingested: int
    new_ubids_created: int
    auto_linked: int
    sent_to_review: int
    processing_time_ms: int
