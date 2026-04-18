from __future__ import annotations

from collections import deque

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.activity import ActivityEvent
from backend.app.models.entity import Business, SourceRecord
from backend.app.models.match import MatchPair
from backend.app.models.review import ReviewTask
from backend.app.schemas.graph import (
    EntityGraphResponse,
    GraphEdgeResponse,
    GraphHotspotResponse,
    GraphMetricsResponse,
    GraphNodeResponse,
    GraphOverviewResponse,
)
from backend.app.services.entity_resolution import find_business_by_token, format_ubid


def _business_node_id(ubid) -> str:
    return f"business:{ubid}"


def _record_node_id(record_id) -> str:
    return f"record:{record_id}"


def _activity_node_id(event_id) -> str:
    return f"activity:{event_id}"


def _review_node_id(task_id) -> str:
    return f"review:{task_id}"


def _calculate_component_metrics(nodes: list[str], edges: list[tuple[str, str]]) -> tuple[int, int]:
    if not nodes:
        return 0, 0

    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for source, target in edges:
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    visited: set[str] = set()
    components = 0
    largest = 0
    for node in adjacency:
        if node in visited:
            continue
        components += 1
        queue = deque([node])
        size = 0
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            size += 1
            queue.extend(neighbour for neighbour in adjacency[current] if neighbour not in visited)
        largest = max(largest, size)
    return components, largest


def _build_overview_metrics(
    businesses: list[Business],
    records: list[SourceRecord],
    events: list[ActivityEvent],
    review_tasks: list[ReviewTask],
    match_pairs: list[MatchPair],
) -> GraphMetricsResponse:
    business_nodes = [_business_node_id(business.ubid) for business in businesses]
    record_nodes = [_record_node_id(record.id) for record in records]
    activity_nodes = [_activity_node_id(event.id) for event in events]
    review_nodes = [_review_node_id(task.id) for task in review_tasks]

    edges: list[tuple[str, str]] = []
    for record in records:
        if record.ubid is not None:
            edges.append((_business_node_id(record.ubid), _record_node_id(record.id)))
    for event in events:
        edges.append((_business_node_id(event.ubid), _activity_node_id(event.id)))
    review_by_pair = {task.match_pair_id: task for task in review_tasks}
    for pair in match_pairs:
        edges.append((_record_node_id(pair.record_a_id), _record_node_id(pair.record_b_id)))
        if pair.id in review_by_pair:
            review_node_id = _review_node_id(review_by_pair[pair.id].id)
            edges.append((review_node_id, _record_node_id(pair.record_a_id)))
            edges.append((review_node_id, _record_node_id(pair.record_b_id)))

    component_nodes = business_nodes + record_nodes + activity_nodes + review_nodes
    connected_components, largest_component_size = _calculate_component_metrics(component_nodes, edges)

    return GraphMetricsResponse(
        node_count=len(component_nodes),
        edge_count=len(edges),
        business_count=len(businesses),
        source_record_count=len(records),
        activity_event_count=len(events),
        open_review_count=len(review_tasks),
        connected_components=connected_components,
        largest_component_size=largest_component_size,
    )


def get_graph_overview(session: Session) -> GraphOverviewResponse:
    businesses = session.execute(
        select(Business).options(selectinload(Business.source_records), selectinload(Business.activity_events))
    ).scalars().all()
    visible_businesses = [business for business in businesses if any(record.ubid == business.ubid for record in business.source_records)]
    records = session.execute(select(SourceRecord)).scalars().all()
    events = session.execute(select(ActivityEvent)).scalars().all()
    review_tasks = session.execute(select(ReviewTask).where(ReviewTask.status == "OPEN")).scalars().all()
    match_pairs = session.execute(select(MatchPair).options(selectinload(MatchPair.review_tasks))).scalars().all()

    open_review_by_pair = {task.match_pair_id for task in review_tasks}

    hotspots: list[GraphHotspotResponse] = []
    for business in visible_businesses:
        linked_records = [record for record in business.source_records if record.ubid == business.ubid]
        linked_record_ids = {record.id for record in linked_records}
        open_review_count = sum(
            1
            for pair in match_pairs
            if pair.id in open_review_by_pair and (pair.record_a_id in linked_record_ids or pair.record_b_id in linked_record_ids)
        )
        risk_score = len(linked_records) + (open_review_count * 3) + min(len(business.activity_events), 5)
        hotspots.append(
            GraphHotspotResponse(
                ubid=format_ubid(business.ubid) or "",
                canonical_name=business.canonical_name,
                status=business.status,
                linked_record_count=len(linked_records),
                activity_count=len(business.activity_events),
                open_review_count=open_review_count,
                risk_score=risk_score,
            )
        )

    hotspots.sort(key=lambda item: (-item.risk_score, -item.linked_record_count, item.canonical_name))

    return GraphOverviewResponse(
        metrics=_build_overview_metrics(visible_businesses, records, events, review_tasks, match_pairs),
        hotspots=hotspots[:8],
    )


def get_entity_graph(session: Session, ubid_token: str) -> EntityGraphResponse:
    business_ref = find_business_by_token(session, ubid_token)
    if business_ref is None:
        raise LookupError("Business not found.")

    business = session.execute(
        select(Business)
        .options(selectinload(Business.source_records), selectinload(Business.activity_events))
        .where(Business.ubid == business_ref.ubid)
    ).scalar_one()

    linked_records = [record for record in business.source_records if record.ubid == business.ubid]
    linked_record_ids = {record.id for record in linked_records}
    pairs = session.execute(
        select(MatchPair)
        .options(
            selectinload(MatchPair.record_a).selectinload(SourceRecord.business),
            selectinload(MatchPair.record_b).selectinload(SourceRecord.business),
            selectinload(MatchPair.review_tasks),
        )
        .where(or_(MatchPair.record_a_id.in_(linked_record_ids), MatchPair.record_b_id.in_(linked_record_ids)))
    ).scalars().all()

    node_map: dict[str, GraphNodeResponse] = {}
    edges: list[GraphEdgeResponse] = []

    focus_id = _business_node_id(business.ubid)
    node_map[focus_id] = GraphNodeResponse(
        id=focus_id,
        label=business.canonical_name,
        node_type="business",
        subtitle=format_ubid(business.ubid),
        status=business.status,
        emphasis="focus",
    )

    for record in linked_records:
        record_id = _record_node_id(record.id)
        node_map[record_id] = GraphNodeResponse(
            id=record_id,
            label=record.raw_name,
            node_type="record",
            subtitle=record.source_system,
            emphasis="primary",
        )
        edges.append(
            GraphEdgeResponse(
                source=focus_id,
                target=record_id,
                edge_type="contains_record",
                label="linked record",
            )
        )

    for event in sorted(business.activity_events, key=lambda item: item.event_date, reverse=True)[:6]:
        activity_id = _activity_node_id(event.id)
        node_map[activity_id] = GraphNodeResponse(
            id=activity_id,
            label=event.event_type.title(),
            node_type="activity",
            subtitle=f"{event.source} | {event.event_date.isoformat()}",
        )
        edges.append(
            GraphEdgeResponse(
                source=focus_id,
                target=activity_id,
                edge_type="activity_signal",
                label="activity",
            )
        )

    for pair in pairs:
        local_record = pair.record_a if pair.record_a_id in linked_record_ids else pair.record_b
        remote_record = pair.record_b if local_record.id == pair.record_a_id else pair.record_a
        local_record_id = _record_node_id(local_record.id)
        remote_record_id = _record_node_id(remote_record.id)

        if remote_record.id not in linked_record_ids:
            node_map.setdefault(
                remote_record_id,
                GraphNodeResponse(
                    id=remote_record_id,
                    label=remote_record.raw_name,
                    node_type="record",
                    subtitle=remote_record.source_system,
                    emphasis="candidate",
                ),
            )

        edges.append(
            GraphEdgeResponse(
                source=local_record_id,
                target=remote_record_id,
                edge_type="match_pair",
                label=pair.decision.replace("_", " ").title(),
                decision=pair.decision,
                confidence=pair.confidence,
            )
        )

        if remote_record.business is not None and remote_record.business.ubid != business.ubid:
            remote_business_id = _business_node_id(remote_record.business.ubid)
            node_map.setdefault(
                remote_business_id,
                GraphNodeResponse(
                    id=remote_business_id,
                    label=remote_record.business.canonical_name,
                    node_type="business",
                    subtitle=format_ubid(remote_record.business.ubid),
                    status=remote_record.business.status,
                    emphasis="related",
                ),
            )
            edges.append(
                GraphEdgeResponse(
                    source=remote_business_id,
                    target=remote_record_id,
                    edge_type="contains_record",
                    label="linked record",
                )
            )

        for task in pair.review_tasks:
            if task.status != "OPEN":
                continue
            review_id = _review_node_id(task.id)
            node_map.setdefault(
                review_id,
                GraphNodeResponse(
                    id=review_id,
                    label="Open Review",
                    node_type="review",
                    subtitle="Human decision required",
                    emphasis="alert",
                ),
            )
            edges.append(
                GraphEdgeResponse(
                    source=review_id,
                    target=local_record_id,
                    edge_type="review_task",
                    label="reviewing",
                )
            )
            edges.append(
                GraphEdgeResponse(
                    source=review_id,
                    target=remote_record_id,
                    edge_type="review_task",
                    label="reviewing",
                )
            )

    nodes = list(node_map.values())
    node_ids = [node.id for node in nodes]
    connected_components, largest_component_size = _calculate_component_metrics(
        node_ids, [(edge.source, edge.target) for edge in edges]
    )
    metrics = GraphMetricsResponse(
        node_count=len(nodes),
        edge_count=len(edges),
        business_count=len([node for node in nodes if node.node_type == "business"]),
        source_record_count=len([node for node in nodes if node.node_type == "record"]),
        activity_event_count=len([node for node in nodes if node.node_type == "activity"]),
        open_review_count=len([node for node in nodes if node.node_type == "review"]),
        connected_components=connected_components,
        largest_component_size=largest_component_size,
    )

    return EntityGraphResponse(
        focus_ubid=format_ubid(business.ubid) or "",
        canonical_name=business.canonical_name,
        metrics=metrics,
        nodes=nodes,
        edges=edges,
    )
