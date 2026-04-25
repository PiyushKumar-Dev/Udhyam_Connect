from __future__ import annotations

import csv
from datetime import date, timedelta
from io import StringIO
import json
from pathlib import Path
import random
import string

from faker import Faker
from sqlalchemy import func, select

from backend.app.database import SessionLocal
from backend.app.models.activity import ActivityEvent
from backend.app.models.entity import Business, SourceRecord
from backend.app.models.match import MatchPair
from backend.app.models.review import ReviewTask
from backend.app.services.entity_resolution import (
    apply_activity_status,
    ingest_records,
    normalise_source_system,
)

SEED = 42
TOTAL_BUSINESSES = 200
TOTAL_EVENTS = 500
BASE_DIR = Path(__file__).resolve().parent
faker = Faker("en_IN")
Faker.seed(SEED)
random.seed(SEED)

PREFIXES = [
    "Tech",
    "Sri",
    "Om",
    "Sai",
    "Balaji",
    "Nandi",
    "Kaveri",
    "Deccan",
    "Info",
    "Wipro",
    "Reliance",
    "Tata",
    "Birla",
    "Mahindra",
    "Adani",
    "Kiran",
    "Bharath",
    "Hindustan",
    "Global",
    "Apex",
]
MIDDLES = [
    "Enterprises",
    "Industries",
    "Technologies",
    "Solutions",
    "Services",
    "Traders",
    "Consulting",
    "Ventures",
    "Systems",
    "Infotech",
]
SECTORS = [
    "Software",
    "Hardware",
    "Retail",
    "Manufacturing",
    "Logistics",
    "Textiles",
    "Pharma",
    "Automotive",
    "Electronics",
    "Foods",
]
ROADS = ["MG", "Park", "Station", "Lake", "Temple", "Market", "Canal", "Airport", "Garden", "College"]
AREAS = ["Nagar", "Layout", "Enclave", "Extension", "Bazaar", "Colony"]
EVENT_SOURCES = ["MUNICIPAL", "UTILITY", "GST", "MCA", "FIRE", "LABOUR", "POLLUTION"]
PRIMARY_SOURCE_QUOTAS = {"MCA": 35, "GST": 65, "MUNICIPAL": 100}
SUPPLEMENT_PLANS = {
    "AUTO_GST": {"count": 15, "source": "GST"},
    "REVIEW_MUNICIPAL": {"count": 20, "source": "MUNICIPAL"},
    "REVIEW_MCA": {"count": 10, "source": "MCA"},
    "EXTRA_MCA": {"count": 5, "source": "MCA"},
    "UTILITY_ACCOUNTS": {"count": 18, "source": "UTILITY"},
    "FIRE_NOC": {"count": 14, "source": "FIRE"},
    "LABOUR_LICENSE": {"count": 16, "source": "LABOUR"},
    "POLLUTION_CLEARANCE": {"count": 12, "source": "POLLUTION"},
}


def _random_pan() -> str:
    letters = "".join(random.choices(string.ascii_uppercase, k=5))
    numbers = "".join(random.choices(string.digits, k=4))
    tail = random.choice(string.ascii_uppercase)
    return f"{letters}{numbers}{tail}"


def _random_gstin(pan: str) -> str:
    state_code = f"{random.randint(1, 35):02d}"
    entity_code = random.choice(string.digits + string.ascii_uppercase)
    checksum = random.choice(string.ascii_uppercase + string.digits)
    return f"{state_code}{pan}{entity_code}Z{checksum}"


def _license_ids(seed_id: str) -> list[str]:
    total = random.randint(1, 2)
    return [f"LIC-{seed_id[-3:]}-{index + 1}" for index in range(total)]


def _base_business_name(index: int) -> str:
    return f"{PREFIXES[index % len(PREFIXES)]} {MIDDLES[(index * 3) % len(MIDDLES)]} {SECTORS[(index * 5) % len(SECTORS)]}"


def _short_initials(name: str) -> str:
    tokens = name.split()[:3]
    return ".".join(token[0] for token in tokens if token) + "."


def _base_address(index: int) -> dict[str, str]:
    house_no = str(10 + (index % 89))
    road = random.choice(ROADS)
    area = random.choice(AREAS)
    city = "Bengaluru"
    state = "Karnataka"
    pincode = f"560{random.randint(1, 107):03d}"
    return {
        "house_no": house_no,
        "road": road,
        "area": area,
        "city": city,
        "state": state,
        "pincode": pincode,
    }


def _address_variant(base_address: dict[str, str], mode: str) -> str:
    house = base_address["house_no"]
    road = base_address["road"]
    area = base_address["area"]
    city = base_address["city"]
    state = base_address["state"]
    pincode = base_address["pincode"]
    if mode == "review":
        return f"{house}, {road} Rd near {area}, {city}, {state} {pincode}"
    if mode == "auto":
        return f"No.{house}, {road}. Road, {area} {city} - {pincode}"
    if mode == "compact":
        return f"{house} {road} Rd, {area}, {city} {pincode}"
    return f"{house} {road} Road, {area}, {city}, {state} {pincode}"


def _name_variant(base_name: str, mode: str) -> str:
    if mode == "review":
        return f"{base_name} Pvt Ltd"
    if mode == "auto":
        return f"{base_name} Private Limited"
    if mode == "initials":
        return f"{_short_initials(base_name)} Pvt. Ltd"
    return f"{base_name} Pvt Ltd"


def _primary_record_payload(business: dict, source_system: str) -> dict:
    payload = {
        "source_uid": f"{source_system}-{business['business_seed_id']}-P0",
        "source_system": source_system,
        "business_seed_id": business["business_seed_id"],
        "raw_name": _name_variant(
            business["base_name"],
            "initials" if source_system == "MCA" and business["index"] % 7 == 0 else "default",
        ),
        "raw_address": _address_variant(
            business["base_address"],
            "compact" if source_system == "GST" else "default",
        ),
        "pan": business["pan"] if source_system != "MUNICIPAL" or business["index"] % 5 != 0 else None,
        "gstin": business["gstin"] if source_system == "GST" else (business["gstin"] if business["index"] % 6 == 0 else None),
        "license_id": business["license_ids"][0] if source_system == "MUNICIPAL" else None,
    }
    return payload


def _supplemental_record_payload(business: dict, source_system: str, mode: str, suffix: str) -> dict:
    payload = {
        "source_uid": f"{source_system}-{business['business_seed_id']}-{suffix}",
        "source_system": source_system,
        "business_seed_id": business["business_seed_id"],
        "raw_name": _name_variant(business["base_name"], "review" if mode == "review" else "auto"),
        "raw_address": _address_variant(
            business["base_address"],
            "review" if mode == "review" else "auto",
        ),
        "pan": business["pan"],
        "gstin": business["gstin"] if source_system == "GST" else business.get("gstin"),
        "license_ids": business["license_ids"],
    }

    if mode == "review":
        payload["pan"] = None
        if source_system != "GST":
            payload["gstin"] = None

    if source_system == "UTILITY":
        payload["service_connection_id"] = f"UTIL-{business['business_seed_id'][-3:]}-{suffix}"
        payload["meter_no"] = f"MTR{business['index'] + 10000}"
        payload["sanction_load_kw"] = 10 + (business["index"] % 40)
    elif source_system == "FIRE":
        payload["noc_id"] = f"FIRE-NOC-{business['business_seed_id'][-3:]}-{suffix}"
        payload["issuing_department"] = "Fire and Emergency Services"
        payload["risk_category"] = random.choice(["LOW", "MODERATE", "HIGH"])
    elif source_system == "LABOUR":
        payload["establishment_code"] = f"LAB-{business['business_seed_id'][-3:]}-{suffix}"
        payload["issuing_department"] = "Labour Department"
        payload["employee_band"] = random.choice(["1-10", "11-25", "26-50", "51-100"])
    elif source_system == "POLLUTION":
        payload["consent_id"] = f"PCB-{business['business_seed_id'][-3:]}-{suffix}"
        payload["issuing_department"] = "Pollution Control Board"
        payload["compliance_band"] = random.choice(["GREEN", "ORANGE", "RED"])
    return payload


def _make_businesses() -> list[dict]:
    businesses: list[dict] = []
    used_names: set[str] = set()
    for index in range(TOTAL_BUSINESSES):
        base_name = _base_business_name(index)
        while base_name in used_names:
            base_name = f"{base_name} {random.choice(string.ascii_uppercase)}"
        used_names.add(base_name)
        pan = _random_pan()
        business_seed_id = f"BIZ-{index + 1:03d}"
        businesses.append(
            {
                "index": index,
                "business_seed_id": business_seed_id,
                "base_name": base_name,
                "base_address": _base_address(index),
                "pan": pan,
                "gstin": _random_gstin(pan),
                "license_ids": _license_ids(business_seed_id),
                "activity_profile": "ACTIVE" if index < 80 else ("DORMANT" if index < 150 else "CLOSED"),
            }
        )
    return businesses


def _assign_primary_sources(businesses: list[dict]) -> None:
    sources = (
        ["MCA"] * PRIMARY_SOURCE_QUOTAS["MCA"]
        + ["GST"] * PRIMARY_SOURCE_QUOTAS["GST"]
        + ["MUNICIPAL"] * PRIMARY_SOURCE_QUOTAS["MUNICIPAL"]
    )
    random.shuffle(sources)
    for business, source in zip(businesses, sources, strict=True):
        business["primary_source"] = source


def _pick_businesses(
    businesses: list[dict],
    count: int,
    required_source: str,
    selected_ids: set[str],
) -> list[dict]:
    candidates = [
        business
        for business in businesses
        if business["business_seed_id"] not in selected_ids and business["primary_source"] != required_source
    ]
    picked = candidates[:count]
    selected_ids.update(business["business_seed_id"] for business in picked)
    return picked


def _build_source_records(businesses: list[dict]) -> list[dict]:
    records = [_primary_record_payload(business, business["primary_source"]) for business in businesses]
    selected_ids: set[str] = set()

    auto_gst = _pick_businesses(businesses, SUPPLEMENT_PLANS["AUTO_GST"]["count"], "GST", selected_ids)
    for business in auto_gst:
        records.append(_supplemental_record_payload(business, "GST", "auto", "S1"))

    review_municipal = _pick_businesses(
        businesses,
        SUPPLEMENT_PLANS["REVIEW_MUNICIPAL"]["count"],
        "MUNICIPAL",
        selected_ids,
    )
    for business in review_municipal:
        records.append(_supplemental_record_payload(business, "MUNICIPAL", "review", "S2"))

    review_mca = _pick_businesses(businesses, SUPPLEMENT_PLANS["REVIEW_MCA"]["count"], "MCA", selected_ids)
    for business in review_mca:
        records.append(_supplemental_record_payload(business, "MCA", "review", "S3"))

    extra_mca = _pick_businesses(businesses, SUPPLEMENT_PLANS["EXTRA_MCA"]["count"], "MCA", selected_ids)
    for business in extra_mca:
        records.append(_supplemental_record_payload(business, "MCA", "auto", "S4"))

    utility_accounts = _pick_businesses(businesses, SUPPLEMENT_PLANS["UTILITY_ACCOUNTS"]["count"], "UTILITY", selected_ids)
    for business in utility_accounts:
        records.append(_supplemental_record_payload(business, "UTILITY", "auto", "S5"))

    fire_noc = _pick_businesses(businesses, SUPPLEMENT_PLANS["FIRE_NOC"]["count"], "FIRE", selected_ids)
    for business in fire_noc:
        records.append(_supplemental_record_payload(business, "FIRE", "auto", "S6"))

    labour_license = _pick_businesses(businesses, SUPPLEMENT_PLANS["LABOUR_LICENSE"]["count"], "LABOUR", selected_ids)
    for business in labour_license:
        records.append(_supplemental_record_payload(business, "LABOUR", "review", "S7"))

    pollution_clearance = _pick_businesses(
        businesses,
        SUPPLEMENT_PLANS["POLLUTION_CLEARANCE"]["count"],
        "POLLUTION",
        selected_ids,
    )
    for business in pollution_clearance:
        records.append(_supplemental_record_payload(business, "POLLUTION", "auto", "S8"))

    return records


def _build_activity_events(businesses: list[dict]) -> list[dict]:
    events: list[dict] = []
    today = date.today()
    for business in businesses:
        seed_id = business["business_seed_id"]
        if business["activity_profile"] == "ACTIVE":
            events.extend(
                [
                    {
                        "business_seed_id": seed_id,
                        "event_type": "RENEWAL",
                        "event_date": (today - timedelta(days=random.randint(20, 140))).isoformat(),
                        "source": "MUNICIPAL",
                        "summary": "Trade license renewed for the current cycle.",
                    },
                    {
                        "business_seed_id": seed_id,
                        "event_type": "INSPECTION",
                        "event_date": (today - timedelta(days=random.randint(10, 170))).isoformat(),
                        "source": "MCA",
                        "summary": "Routine inspection completed with no major findings.",
                    },
                    {
                        "business_seed_id": seed_id,
                        "event_type": "ELECTRICITY",
                        "event_date": (today - timedelta(days=random.randint(1, 90))).isoformat(),
                        "source": "UTILITY",
                        "summary": "Electricity usage recorded for the latest billing period.",
                    },
                ]
            )
            continue
        if business["activity_profile"] == "DORMANT":
            events.extend(
                [
                    {
                        "business_seed_id": seed_id,
                        "event_type": "COMPLAINT",
                        "event_date": (today - timedelta(days=random.randint(380, 520))).isoformat(),
                        "source": random.choice(EVENT_SOURCES),
                        "summary": "Older complaint archived with no recent follow-up.",
                    },
                    {
                        "business_seed_id": seed_id,
                        "event_type": "INSPECTION",
                        "event_date": (today - timedelta(days=random.randint(410, 700))).isoformat(),
                        "source": "MUNICIPAL",
                        "summary": "Historic inspection record retained for audit purposes.",
                    },
                ]
            )
            continue
        events.extend(
            [
                {
                    "business_seed_id": seed_id,
                    "event_type": "SURRENDERED",
                    "event_date": (today - timedelta(days=random.randint(420, 760))).isoformat(),
                    "source": "MUNICIPAL",
                    "summary": "License surrendered and closure noted by the municipal authority.",
                    "status": "surrendered",
                },
                {
                    "business_seed_id": seed_id,
                    "event_type": "COMPLAINT",
                    "event_date": (today - timedelta(days=random.randint(430, 700))).isoformat(),
                    "source": "MCA",
                    "summary": "Historic closure-related complaint remains on file.",
                },
            ]
        )

    while len(events) < TOTAL_EVENTS:
        business = random.choice(businesses)
        today = date.today()
        if business["activity_profile"] == "ACTIVE":
            events.append(
                {
                    "business_seed_id": business["business_seed_id"],
                    "event_type": random.choice(["ELECTRICITY", "RENEWAL"]),
                    "event_date": (today - timedelta(days=random.randint(1, 150))).isoformat(),
                    "source": random.choice(EVENT_SOURCES),
                    "summary": "Additional recent signal supports active operations.",
                }
            )
        elif business["activity_profile"] == "DORMANT":
            events.append(
                {
                    "business_seed_id": business["business_seed_id"],
                    "event_type": "COMPLAINT",
                    "event_date": (today - timedelta(days=random.randint(380, 780))).isoformat(),
                    "source": random.choice(EVENT_SOURCES),
                    "summary": "Historic issue retained without recent activity.",
                }
            )
        else:
            events.append(
                {
                    "business_seed_id": business["business_seed_id"],
                    "event_type": "CANCELLED",
                    "event_date": (today - timedelta(days=random.randint(430, 820))).isoformat(),
                    "source": "MUNICIPAL",
                    "summary": "Closure record reaffirmed by a cancelled-license event.",
                    "status": "cancelled",
                }
            )
    return events[:TOTAL_EVENTS]


def _export_records(records: list[dict]) -> None:
    mca_records = [record for record in records if record["source_system"] == "MCA"]
    gst_records = [record for record in records if record["source_system"] == "GST"]
    municipal_records = [record for record in records if record["source_system"] == "MUNICIPAL"]
    utility_records = [record for record in records if record["source_system"] == "UTILITY"]
    fire_records = [record for record in records if record["source_system"] == "FIRE"]
    labour_records = [record for record in records if record["source_system"] == "LABOUR"]
    pollution_records = [record for record in records if record["source_system"] == "POLLUTION"]

    try:
        (BASE_DIR / "sample_mca.csv").write_text(_to_csv(mca_records), encoding="utf-8")
        (BASE_DIR / "sample_gst.csv").write_text(_to_csv(gst_records), encoding="utf-8")
        (BASE_DIR / "sample_licenses.json").write_text(
            json.dumps(municipal_records, indent=2),
            encoding="utf-8",
        )
        (BASE_DIR / "sample_utility_accounts.json").write_text(json.dumps(utility_records, indent=2), encoding="utf-8")
        (BASE_DIR / "sample_fire_noc.json").write_text(json.dumps(fire_records, indent=2), encoding="utf-8")
        (BASE_DIR / "sample_labour_registry.json").write_text(json.dumps(labour_records, indent=2), encoding="utf-8")
        (BASE_DIR / "sample_pollution_clearances.json").write_text(
            json.dumps(pollution_records, indent=2),
            encoding="utf-8",
        )
    except PermissionError:
        print("Warning: Could not write sample files (permission denied). Continuing with database seeding...")


def _to_csv(records: list[dict]) -> str:
    if not records:
        return ""
    columns = [
        "source_uid",
        "source_system",
        "business_seed_id",
        "raw_name",
        "raw_address",
        "pan",
        "gstin",
        "license_id",
    ]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for record in records:
        writer.writerow({column: record.get(column) for column in columns})
    return buffer.getvalue()


def _export_events(events: list[dict]) -> None:
    try:
        (BASE_DIR / "sample_events.json").write_text(json.dumps(events, indent=2), encoding="utf-8")
    except PermissionError:
        pass  # Silently ignore if we can't write to the data directory


def _load_exported_records() -> list[dict]:
    records: list[dict] = []
    for filename in ("sample_mca.csv", "sample_gst.csv"):
        with (BASE_DIR / filename).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for item in reader:
                item["pan"] = item["pan"] or None
                item["gstin"] = item["gstin"] or None
                item["license_id"] = item["license_id"] or None
                item["source_system"] = normalise_source_system(str(item["source_system"]))
                records.append(item)
    license_records = json.loads((BASE_DIR / "sample_licenses.json").read_text(encoding="utf-8"))
    for record in license_records:
        record["source_system"] = normalise_source_system(str(record["source_system"]))
        records.append(record)
    for filename in (
        "sample_utility_accounts.json",
        "sample_fire_noc.json",
        "sample_labour_registry.json",
        "sample_pollution_clearances.json",
    ):
        department_records = json.loads((BASE_DIR / filename).read_text(encoding="utf-8"))
        for record in department_records:
            record["source_system"] = normalise_source_system(str(record["source_system"]))
            records.append(record)
    return records


def _load_events() -> list[dict]:
    return json.loads((BASE_DIR / "sample_events.json").read_text(encoding="utf-8"))


def generate_mock_files() -> None:
    businesses = _make_businesses()
    _assign_primary_sources(businesses)
    records = _build_source_records(businesses)
    events = _build_activity_events(businesses)
    _export_records(records)
    _export_events(events)


def seed_database() -> None:
    generate_mock_files()
    session = SessionLocal()
    try:
        existing = session.execute(select(SourceRecord.id).limit(1)).first()
        if not existing:
            records = _load_exported_records()
            summary = ingest_records(session, records, actor="seed")
            print(f"Ingested {summary['records_ingested']} records.")

            all_records = session.execute(select(SourceRecord)).scalars().all()
            business_map: dict[str, object] = {}
            for record in all_records:
                business_seed_id = record.raw_payload.get("business_seed_id")
                if business_seed_id and record.ubid:
                    business_map[str(business_seed_id)] = record.ubid

            events = _load_events()
            for event in events:
                ubid = business_map.get(event["business_seed_id"])
                if ubid is None:
                    continue
                session.add(
                    ActivityEvent(
                        ubid=ubid,
                        event_type=event["event_type"],
                        event_date=date.fromisoformat(event["event_date"]),
                        source=event["source"],
                        payload={
                            "summary": event["summary"],
                            "status": event.get("status"),
                            "business_seed_id": event["business_seed_id"],
                        },
                    )
                )
            session.commit()

            businesses = session.execute(select(Business).where(Business.source_records.any())).scalars().all()
            for business in businesses:
                apply_activity_status(session, business, "seed")
            session.commit()
        else:
            print("Main ingestion skipped: source records already exist.")

        pending_reviews = session.execute(select(ReviewTask).where(ReviewTask.status == "OPEN")).scalars().all()
        pending_pairs = session.execute(select(MatchPair).where(MatchPair.decision == "PENDING")).scalars().all()
        
        # Ensure we show some 'Auto-Linked Today' activity for the demo
        auto_linked_today = session.execute(
            select(func.count(MatchPair.id)).where(
                MatchPair.decision == "AUTO_LINKED",
                func.date(MatchPair.created_at) == date.today()
            )
        ).scalar_one()
        
        if auto_linked_today < 5:
            try:
                print("Adding dummy auto-linked records for dashboard stats...")
                # Pick some existing businesses to link
                biz_records = session.execute(select(SourceRecord).limit(10)).scalars().all()
                for i in range(min(7, len(biz_records) - 1)):
                    session.add(MatchPair(
                        record_a_id=biz_records[i].id,
                        record_b_id=biz_records[i+1].id,
                        confidence=0.95,
                        decision="AUTO_LINKED",
                        evidence={"final": 0.95, "justification": "Seeded for dashboard activity demo."}
                    ))
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Warning: Could not create dummy match records: {e}")

        businesses = session.execute(select(Business).where(Business.source_records.any())).scalars().all()
        print(
            f"Seed completed with {len(businesses)} visible businesses, "
            f"{len(pending_pairs)} pending match pairs, and {len(pending_reviews)} open review tasks."
        )
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
