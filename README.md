# Udhyam Connect

**Live Demo: [https://udhyam-frontend.onrender.com](https://udhyam-frontend.onrender.com)**

---

UBID System is a synthetic-data MVP for resolving business identities across fragmented source systems, classifying operational activity, and routing ambiguous matches into an explainable human review flow. The codebase is modular by design so fraud detection, graph analytics, or downstream scoring services can be added as separate modules without refactoring the ingest or entity core.

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Frontend: React 18, TypeScript, Vite, Tailwind CSS, React Query, Axios
- Data: Faker-generated synthetic businesses, source records, and activity events
- Infra: Docker Compose

## Run

From [ubid-system](</d:/Users/acer/OneDrive/Desktop/udhyam Connect/ubid-system>):

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Tests

Backend tests live under [backend/tests](</d:/Users/acer/OneDrive/Desktop/udhyam Connect/ubid-system/backend/tests>) and use an in-memory SQLite database so the core ingest plus review flow can be validated without starting Docker.

Install dev-only dependencies:

```bash
pip install -r backend/requirements-dev.txt
```

Run the backend suite:

```bash
pytest backend/tests -q
```

## Demo Auth

The app includes a lightweight demo auth layer with role-based access:

- `viewer.demo`: read-only access to dashboard, entity detail, search, stats, and graph
- `analyst.demo`: viewer access plus ingest, review queue, and activity refresh
- `admin.demo`: full demo access

The frontend role switcher stores the selected demo identity locally and sends it to the backend through request headers.

## What Seeds Automatically

On first backend start:

- Alembic migrations run
- `data/seed.py` generates mock export files
- 200 synthetic businesses are created
- 310 source records are ingested across `MCA`, `GST`, `MUNICIPAL`, `UTILITY`, `FIRE`, `LABOUR`, and `POLLUTION`
- 500 activity events are linked and classified
- 30 ambiguous match pairs are left in the review queue

Generated files:

- [sample_mca.csv](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/data/sample_mca.csv)
- [sample_gst.csv](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/data/sample_gst.csv)
- [sample_licenses.json](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/data/sample_licenses.json)
- [sample_utility_accounts.json](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/data/sample_utility_accounts.json)
- [sample_fire_noc.json](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/data/sample_fire_noc.json)
- [sample_labour_registry.json](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/data/sample_labour_registry.json)
- [sample_pollution_clearances.json](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/data/sample_pollution_clearances.json)
- [sample_events.json](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/data/sample_events.json)

## Core Behaviors

- Source payloads are stored intact in `raw_payload`; normalization never mutates source data.
- Match evidence is field-level and exposed through the API and frontend review panel.
- Review decisions are reversible in practice through retained source records plus `audit_log`.
- Rejected pairs are never auto-matched again.
- Re-ingesting records with the same `source_system` plus `source_uid` creates no duplicates.

## API Summary

- `POST /api/ingest`
- `GET /api/auth/me`
- `GET /api/entities`
- `GET /api/entities/{ubid}`
- `GET /api/search?q=`
- `GET /api/matches/pending`
- `POST /api/matches/{match_id}/decide`
- `POST /api/activity/classify`
- `GET /api/stats`
- `GET /api/graph/overview`
- `GET /api/graph/entity/{ubid}`

## Project Layout

- [backend/app/main.py](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/backend/app/main.py)
- [backend/app/services/entity_resolution.py](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/backend/app/services/entity_resolution.py)
- [backend/app/services/graph_analytics.py](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/backend/app/services/graph_analytics.py)
- [backend/app/services/activity_classifier.py](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/backend/app/services/activity_classifier.py)
- [frontend/src/pages/Dashboard.tsx](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/frontend/src/pages/Dashboard.tsx)
- [frontend/src/pages/BusinessProfile.tsx](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/frontend/src/pages/BusinessProfile.tsx)
- [frontend/src/pages/ReviewPanel.tsx](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/frontend/src/pages/ReviewPanel.tsx)
- [frontend/src/pages/GraphExplorer.tsx](/d:/Users/acer/OneDrive/Desktop/udhyam%20Connect/ubid-system/frontend/src/pages/GraphExplorer.tsx)

## Notes

- The backend container uses the repo root as build context so `data/seed.py` and exported mock files are available at startup.
- The system avoids external enrichment services and sends no raw PII outside the local stack.
- `ml/features.py` and `ml/train_classifier.py` are placeholders for learning from review decisions later.
- The dashboard and entity profile now surface anomaly risk based on cross-department linkage, open reviews, and conflicting activity signals.
