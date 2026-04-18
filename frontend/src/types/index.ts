export interface EntitySummary {
  ubid: string;
  canonical_name: string;
  status: "ACTIVE" | "DORMANT" | "CLOSED";
  confidence: number;
  risk: RiskSummary;
  source_count: number;
  updated_at: string;
}

export interface EntityListResponse {
  total: number;
  items: EntitySummary[];
}

export interface SourceRecord {
  id: string;
  source_system: string;
  raw_name: string;
  norm_name: string;
  raw_address: string;
  norm_address: string;
  pan: string | null;
  gstin: string | null;
  license_ids: string[];
  raw_payload: Record<string, unknown>;
  match_confidence?: number | null;
}

export interface ActivityTimelineEvent {
  id: string;
  event_type: string;
  event_date: string;
  source: string;
  payload: Record<string, unknown>;
  summary: string;
}

export interface EntityDetail {
  ubid: string;
  canonical_name: string;
  status: "ACTIVE" | "DORMANT" | "CLOSED";
  status_reason: string;
  confidence: number;
  risk: RiskSummary;
  explanation: string;
  linked_records: SourceRecord[];
  activity_timeline: ActivityTimelineEvent[];
  created_at: string;
  updated_at: string;
}

export interface MatchEvidence {
  name_score: number;
  address_score: number;
  pan_score: number;
  gstin_score: number;
  license_score: number;
  final: number;
  threshold_used: string;
  shared_pan?: string | null;
  shared_gstin?: string | null;
}

export interface MatchPair {
  id: string;
  confidence: number;
  decision: string;
  created_at: string;
  evidence: MatchEvidence;
  explanation: string;
  record_a: SourceRecord;
  record_b: SourceRecord;
}

export interface StatsResponse {
  total_businesses: number;
  active: number;
  dormant: number;
  closed: number;
  pending_review: number;
  auto_linked_today: number;
  high_risk_entities: number;
  source_breakdown: Record<string, number>;
}

export interface MatchDecisionPayload {
  decision: "APPROVE" | "REJECT";
  reviewer: string;
  note: string;
}

export interface GraphMetrics {
  node_count: number;
  edge_count: number;
  business_count: number;
  source_record_count: number;
  activity_event_count: number;
  open_review_count: number;
  connected_components: number;
  largest_component_size: number;
}

export interface GraphHotspot {
  ubid: string;
  canonical_name: string;
  status: "ACTIVE" | "DORMANT" | "CLOSED";
  linked_record_count: number;
  activity_count: number;
  open_review_count: number;
  risk_score: number;
}

export interface GraphNode {
  id: string;
  label: string;
  node_type: "business" | "record" | "activity" | "review";
  subtitle?: string | null;
  status?: "ACTIVE" | "DORMANT" | "CLOSED" | null;
  emphasis?: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  edge_type: string;
  label: string;
  decision?: string | null;
  confidence?: number | null;
}

export interface GraphOverviewResponse {
  metrics: GraphMetrics;
  hotspots: GraphHotspot[];
}

export interface EntityGraphResponse {
  focus_ubid: string;
  canonical_name: string;
  metrics: GraphMetrics;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface RiskSummary {
  score: number;
  level: "LOW" | "MEDIUM" | "HIGH";
  reasons: string[];
}

export interface AuthUser {
  username: string;
  display_name: string;
  role: "viewer" | "analyst" | "admin";
}

export interface PincodeStatsItem {
  pincode: string;
  total: number;
  active: number;
  dormant: number;
  closed: number;
  high_risk: number;
}

export interface PincodeStatsResponse {
  pincodes: PincodeStatsItem[];
  total_pincodes: number;
}
