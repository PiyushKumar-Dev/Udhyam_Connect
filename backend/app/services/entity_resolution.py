from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from copy import deepcopy
from statistics import mean
from time import perf_counter
import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.activity import ActivityEvent
from backend.app.models.entity import AuditLog, Business, SourceRecord
from backend.app.models.match import MatchPair
from backend.app.models.review import ReviewDecision, ReviewTask
from backend.app.services.activity_classifier import classify
from backend.app.services.confidence import AUTO_LINK_THRESHOLD, REVIEW_THRESHOLD, compute_match_evidence
from backend.app.services.explainer import generate_explanation
from backend.app.utils.blocking import generate_blocking_keys
from backend.app.utils.normalise import normalise_address, normalise_name

SOURCE_SYSTEMS = {"MCA", "GST", "MUNICIPAL", "UTILITY", "FIRE", "LABOUR", "POLLUTION"}
VISIBLE_MATCH_DECISIONS = {"AUTO_LINKED", "APPROVED"}


def format_ubid(value: uuid.UUID | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        parsed = uuid.UUID(value)
    else:
        parsed = value
    return f"UBID-{str(parsed).split('-')[0].upper()}"


def source_record_snapshot(record: SourceRecord) -> dict:
    return {
        "id": str(record.id),
        "source_system": record.source_system,
        "raw_name": record.raw_name,
        "norm_name": record.norm_name,
        "raw_address": record.raw_address,
        "norm_address": record.norm_address,
        "pan": record.pan,
        "gstin": record.gstin,
        "license_ids": list(record.license_ids or []),
        "ubid": format_ubid(record.ubid),
    }


def business_snapshot(business: Business) -> dict:
    return {
        "ubid": format_ubid(business.ubid),
        "canonical_name": business.canonical_name,
        "status": business.status,
        "status_reason": business.status_reason,
        "confidence": business.confidence,
    }


def match_pair_snapshot(match_pair: MatchPair) -> dict:
    return {
        "id": str(match_pair.id),
        "record_a_id": str(match_pair.record_a_id),
        "record_b_id": str(match_pair.record_b_id),
        "confidence": match_pair.confidence,
        "decision": match_pair.decision,
        "evidence": deepcopy(match_pair.evidence),
    }


def review_task_snapshot(task: ReviewTask) -> dict:
    return {
        "id": str(task.id),
        "match_pair_id": str(task.match_pair_id),
        "status": task.status,
        "assigned_to": task.assigned_to,
    }


def log_audit(
    session: Session,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before_state: dict,
    after_state: dict,
    actor: str,
) -> None:
    session.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state,
            actor=actor,
        )
    )


def extract_source_uid(payload: dict) -> str | None:
    for key in ("source_uid", "record_id", "id", "license_id"):
        value = payload.get(key)
        if value:
            return str(value)
    return None


def normalise_source_system(value: str) -> str:
    upper = value.upper()
    if upper in SOURCE_SYSTEMS:
        return upper
    if "FIRE" in upper or "NOC" in upper:
        return "FIRE"
    if "LABOUR" in upper or "LABOR" in upper or "SHOP" in upper:
        return "LABOUR"
    if "POLLUTION" in upper or "PCB" in upper or "CONSENT" in upper:
        return "POLLUTION"
    if "LICENSE" in upper:
        return "MUNICIPAL"
    return upper or "MUNICIPAL"


def _clean_optional(value: object, length: int | None = None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    if not text or text in {"NONE", "NAN", "NULL"}:
        return None
    if length:
        return text[:length]
    return text


def _coerce_license_ids(payload: dict) -> list[str]:
    if isinstance(payload.get("license_ids"), list):
        return [str(item) for item in payload["license_ids"] if item]
    if payload.get("license_id"):
        return [str(payload["license_id"])]
    return []


def make_source_record(source_system: str, payload: dict) -> SourceRecord:
    raw_name = str(
        payload.get("raw_name")
        or payload.get("name")
        or payload.get("business_name")
        or payload.get("legal_name")
        or "Unknown Business"
    )
    raw_address = str(payload.get("raw_address") or payload.get("address") or payload.get("registered_address") or "")
    return SourceRecord(
        source_system=normalise_source_system(source_system),
        raw_name=raw_name,
        norm_name=normalise_name(raw_name),
        raw_address=raw_address,
        norm_address=normalise_address(raw_address),
        pan=_clean_optional(payload.get("pan"), 10),
        gstin=_clean_optional(payload.get("gstin"), 15),
        license_ids=_coerce_license_ids(payload),
        raw_payload=deepcopy(payload),
    )


def build_blocking_index(records: Iterable[SourceRecord]) -> tuple[dict[uuid.UUID, SourceRecord], dict[str, set[uuid.UUID]]]:
    record_map: dict[uuid.UUID, SourceRecord] = {}
    blocking_index: dict[str, set[uuid.UUID]] = defaultdict(set)
    for record in records:
        if record.ubid is None:
            continue
        record_map[record.id] = record
        for key in generate_blocking_keys(record):
            blocking_index[key].add(record.id)
    return record_map, blocking_index


def find_match_pair(session: Session, record_a_id: uuid.UUID, record_b_id: uuid.UUID) -> MatchPair | None:
    query = select(MatchPair).where(
        or_(
            and_(MatchPair.record_a_id == record_a_id, MatchPair.record_b_id == record_b_id),
            and_(MatchPair.record_a_id == record_b_id, MatchPair.record_b_id == record_a_id),
        )
    )
    return session.execute(query).scalar_one_or_none()


def ensure_review_task(session: Session, match_pair: MatchPair) -> ReviewTask:
    task = session.execute(
        select(ReviewTask).where(ReviewTask.match_pair_id == match_pair.id, ReviewTask.status == "OPEN")
    ).scalar_one_or_none()
    if task:
        return task
    task = ReviewTask(match_pair_id=match_pair.id, status="OPEN")
    session.add(task)
    session.flush()
    return task


def refresh_business_projection(session: Session, business: Business, actor: str) -> None:
    records = [record for record in business.source_records if record.ubid == business.ubid]
    if not records:
        return
    before = business_snapshot(business)
    business.canonical_name = max((record.norm_name for record in records), key=len)

    linked_record_ids = {record.id for record in records}
    pairs = session.execute(
        select(MatchPair).options(selectinload(MatchPair.record_a), selectinload(MatchPair.record_b))
    ).scalars()
    confidences = [
        pair.confidence
        for pair in pairs
        if pair.decision in VISIBLE_MATCH_DECISIONS
        and pair.record_a_id in linked_record_ids
        and pair.record_b_id in linked_record_ids
    ]
    business.confidence = round(mean(confidences), 4) if confidences else 1.0
    session.flush()
    after = business_snapshot(business)
    if before != after:
        log_audit(session, "BUSINESS_UPDATED", "business", business.ubid, before, after, actor)


def create_business_for_record(
    session: Session,
    record: SourceRecord,
    actor: str,
    confidence: float = 1.0,
) -> Business:
    business = Business(
        canonical_name=record.norm_name,
        status="DORMANT",
        status_reason="Awaiting activity classification.",
        confidence=confidence,
    )
    session.add(business)
    session.flush()
    log_audit(session, "BUSINESS_CREATED", "business", business.ubid, {}, business_snapshot(business), actor)
    assign_record_to_business(session, record, business, actor)
    refresh_business_projection(session, business, actor)
    return business


def assign_record_to_business(session: Session, record: SourceRecord, business: Business, actor: str) -> None:
    before = source_record_snapshot(record)
    record.ubid = business.ubid
    session.flush()
    after = source_record_snapshot(record)
    if before != after:
        log_audit(session, "UBID_ASSIGNED", "source_record", record.id, before, after, actor)


def upsert_match_pair(
    session: Session,
    record_a: SourceRecord,
    record_b: SourceRecord,
    evidence: dict,
    decision: str,
) -> MatchPair:
    existing = find_match_pair(session, record_a.id, record_b.id)
    if existing:
        before = match_pair_snapshot(existing)
        existing.confidence = evidence["final"]
        existing.evidence = deepcopy(evidence)
        existing.decision = decision
        session.flush()
        after = match_pair_snapshot(existing)
        if before != after:
            log_audit(session, "MATCH_UPDATED", "match_pair", existing.id, before, after, "system")
        return existing

    ordered_records = sorted([record_a, record_b], key=lambda item: str(item.id))
    match_pair = MatchPair(
        record_a_id=ordered_records[0].id,
        record_b_id=ordered_records[1].id,
        confidence=evidence["final"],
        decision=decision,
        evidence=deepcopy(evidence),
    )
    session.add(match_pair)
    session.flush()
    log_audit(session, "MATCH_CREATED", "match_pair", match_pair.id, {}, match_pair_snapshot(match_pair), "system")
    return match_pair


def ingest_records(session: Session, payloads: list[dict], actor: str = "system") -> dict[str, int]:
    started = perf_counter()
    existing_records = session.execute(select(SourceRecord)).scalars().all()
    dedupe_keys = {
        (record.source_system, extract_source_uid(record.raw_payload))
        for record in existing_records
        if extract_source_uid(record.raw_payload)
    }
    record_map, blocking_index = build_blocking_index(existing_records)

    summary = {
        "records_ingested": 0,
        "new_ubids_created": 0,
        "auto_linked": 0,
        "sent_to_review": 0,
    }

    for payload in payloads:
        source_system = normalise_source_system(str(payload.get("source_system") or "MUNICIPAL"))
        source_uid = extract_source_uid(payload)
        dedupe_key = (source_system, source_uid)
        if source_uid and dedupe_key in dedupe_keys:
            continue

        record = make_source_record(source_system, payload)
        session.add(record)
        session.flush()
        summary["records_ingested"] += 1
        if source_uid:
            dedupe_keys.add(dedupe_key)

        candidate_ids: set[uuid.UUID] = set()
        for key in generate_blocking_keys(record):
            candidate_ids.update(blocking_index.get(key, set()))

        best_candidate: SourceRecord | None = None
        best_evidence: dict | None = None
        for candidate_id in candidate_ids:
            candidate = record_map[candidate_id]
            existing_match = find_match_pair(session, record.id, candidate.id)
            if existing_match and existing_match.decision == "REJECTED":
                continue
            evidence = compute_match_evidence(record, candidate)
            if best_evidence is None or evidence["final"] > best_evidence["final"]:
                best_candidate = candidate
                best_evidence = evidence

        if best_candidate and best_evidence and best_evidence["final"] >= AUTO_LINK_THRESHOLD:
            upsert_match_pair(session, record, best_candidate, best_evidence, "AUTO_LINKED")
            target_business = best_candidate.business
            if target_business is None:
                target_business = create_business_for_record(session, best_candidate, actor, best_evidence["final"])
                summary["new_ubids_created"] += 1
            assign_record_to_business(session, record, target_business, actor)
            refresh_business_projection(session, target_business, actor)
            record_map[record.id] = record
            for key in generate_blocking_keys(record):
                blocking_index[key].add(record.id)
            summary["auto_linked"] += 1
            continue

        if best_candidate and best_evidence and REVIEW_THRESHOLD <= best_evidence["final"] < AUTO_LINK_THRESHOLD:
            match_pair = upsert_match_pair(session, record, best_candidate, best_evidence, "PENDING")
            ensure_review_task(session, match_pair)
            summary["sent_to_review"] += 1
            continue

        business = create_business_for_record(session, record, actor)
        summary["new_ubids_created"] += 1
        record_map[record.id] = record
        for key in generate_blocking_keys(record):
            blocking_index[key].add(record.id)
        refresh_business_projection(session, business, actor)

    session.commit()
    summary["processing_time_ms"] = int((perf_counter() - started) * 1000)
    return summary


def find_business_by_token(session: Session, ubid_token: str) -> Business | None:
    token = ubid_token.strip().upper()
    if token.startswith("UBID-"):
        token = token.split("UBID-")[-1]
        businesses = session.execute(select(Business).where(Business.source_records.any())).scalars().all()
        for business in businesses:
            if str(business.ubid).split("-")[0].upper() == token:
                return business
        return None
    try:
        parsed = uuid.UUID(ubid_token)
    except ValueError:
        return None
    return session.get(Business, parsed)


def get_record_match_confidence(session: Session, record: SourceRecord) -> float | None:
    pairs = session.execute(
        select(MatchPair).where(
            or_(MatchPair.record_a_id == record.id, MatchPair.record_b_id == record.id),
            MatchPair.decision.in_(VISIBLE_MATCH_DECISIONS),
        )
    ).scalars().all()
    if not pairs:
        return None
    return round(max(pair.confidence for pair in pairs), 4)


def get_business_explanation(session: Session, business: Business) -> str:
    linked_ids = {record.id for record in business.source_records if record.ubid == business.ubid}
    if len(linked_ids) <= 1:
        return "Single-source business entity with no cross-record link needed."
    pairs = session.execute(select(MatchPair)).scalars().all()
    visible_pairs = [
        pair
        for pair in pairs
        if pair.decision in VISIBLE_MATCH_DECISIONS
        and pair.record_a_id in linked_ids
        and pair.record_b_id in linked_ids
    ]
    if not visible_pairs:
        return "Linked entity assembled from approved source records."
    best_pair = max(visible_pairs, key=lambda item: item.confidence)
    return generate_explanation(best_pair.evidence)


def apply_activity_status(session: Session, business: Business, actor: str) -> dict:
    events = session.execute(
        select(ActivityEvent).where(ActivityEvent.ubid == business.ubid).order_by(ActivityEvent.event_date.desc())
    ).scalars().all()
    result = classify(business.ubid, events)
    before = business_snapshot(business)
    business.status = result.status
    business.status_reason = result.reason
    session.flush()
    after = business_snapshot(business)
    if before != after:
        log_audit(session, "STATUS_UPDATED", "business", business.ubid, before, after, actor)
    return {
        "ubid": result.ubid,
        "status": result.status,
        "reason": result.reason,
        "last_event_date": result.last_event_date,
        "event_count": result.event_count,
        "timeline": [
            {"date": item.date, "type": item.type, "source": item.source, "summary": item.summary}
            for item in result.timeline
        ],
    }


def merge_businesses(session: Session, target: Business, source: Business, actor: str) -> Business:
    if target.ubid == source.ubid:
        return target
    before_source = business_snapshot(source)
    before_target = business_snapshot(target)

    source_records = session.execute(select(SourceRecord).where(SourceRecord.ubid == source.ubid)).scalars().all()
    for record in source_records:
        assign_record_to_business(session, record, target, actor)

    source_events = session.execute(select(ActivityEvent).where(ActivityEvent.ubid == source.ubid)).scalars().all()
    for event in source_events:
        event.ubid = target.ubid

    refresh_business_projection(session, target, actor)
    log_audit(session, "BUSINESS_MERGED", "business", target.ubid, before_target, business_snapshot(target), actor)
    log_audit(
        session,
        "BUSINESS_EMPTIED",
        "business",
        source.ubid,
        before_source,
        {"merged_into": format_ubid(target.ubid)},
        actor,
    )
    return target


def decide_match(
    session: Session,
    match_id: str,
    decision: str,
    reviewer: str,
    note: str,
) -> str | None:
    try:
        parsed_match_id = uuid.UUID(match_id)
    except ValueError as exc:
        raise ValueError("Invalid match identifier.") from exc

    match_pair = session.execute(
        select(MatchPair)
        .options(
            selectinload(MatchPair.record_a).selectinload(SourceRecord.business),
            selectinload(MatchPair.record_b).selectinload(SourceRecord.business),
            selectinload(MatchPair.review_tasks),
        )
        .where(MatchPair.id == parsed_match_id)
    ).scalar_one_or_none()
    if match_pair is None:
        raise LookupError("Match pair not found.")

    task = next((item for item in match_pair.review_tasks if item.status == "OPEN"), None)
    if task is None:
        raise LookupError("Open review task not found.")

    decision_upper = decision.upper()
    record_a = match_pair.record_a
    record_b = match_pair.record_b
    task_before = review_task_snapshot(task)
    match_before = match_pair_snapshot(match_pair)
    resolved_ubid: str | None = None

    if decision_upper == "APPROVE":
        business = record_a.business or record_b.business
        if business is None:
            business = create_business_for_record(session, record_a, reviewer, match_pair.confidence)
        if record_a.ubid != business.ubid:
            assign_record_to_business(session, record_a, business, reviewer)
        if record_b.ubid is None:
            assign_record_to_business(session, record_b, business, reviewer)
        elif record_b.ubid != business.ubid and record_b.business is not None:
            business = merge_businesses(session, business, record_b.business, reviewer)
        refresh_business_projection(session, business, reviewer)
        match_pair.decision = "APPROVED"
        resolved_ubid = format_ubid(business.ubid)
    elif decision_upper == "REJECT":
        if record_a.ubid is None:
            create_business_for_record(session, record_a, reviewer)
        if record_b.ubid is None:
            create_business_for_record(session, record_b, reviewer)
        match_pair.decision = "REJECTED"
    else:
        raise ValueError("Decision must be APPROVE or REJECT.")

    task.status = "RESOLVED"
    review_decision = ReviewDecision(
        task_id=task.id,
        decision=decision_upper,
        reviewer=reviewer,
        note=note,
    )
    session.add(review_decision)
    session.flush()

    log_audit(
        session,
        "REVIEW_TASK_UPDATED",
        "review_task",
        task.id,
        task_before,
        review_task_snapshot(task),
        reviewer,
    )
    log_audit(
        session,
        "MATCH_REVIEWED",
        "match_pair",
        match_pair.id,
        match_before,
        match_pair_snapshot(match_pair),
        reviewer,
    )
    log_audit(
        session,
        "REVIEW_DECISION_CREATED",
        "review_decision",
        review_decision.id,
        {},
        {
            "decision": review_decision.decision,
            "reviewer": review_decision.reviewer,
            "note": review_decision.note,
        },
        reviewer,
    )
    session.commit()
    return resolved_ubid
