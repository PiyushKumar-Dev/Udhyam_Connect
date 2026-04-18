from __future__ import annotations

from pydantic import BaseModel


class GraphMetricsResponse(BaseModel):
    node_count: int
    edge_count: int
    business_count: int
    source_record_count: int
    activity_event_count: int
    open_review_count: int
    connected_components: int
    largest_component_size: int


class GraphHotspotResponse(BaseModel):
    ubid: str
    canonical_name: str
    status: str
    linked_record_count: int
    activity_count: int
    open_review_count: int
    risk_score: int


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    node_type: str
    subtitle: str | None = None
    status: str | None = None
    emphasis: str | None = None


class GraphEdgeResponse(BaseModel):
    source: str
    target: str
    edge_type: str
    label: str
    decision: str | None = None
    confidence: float | None = None


class GraphOverviewResponse(BaseModel):
    metrics: GraphMetricsResponse
    hotspots: list[GraphHotspotResponse]


class EntityGraphResponse(BaseModel):
    focus_ubid: str
    canonical_name: str
    metrics: GraphMetricsResponse
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
