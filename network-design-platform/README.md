# Network Design Platform

A multi-site web replacement for the `CCU_RACKID_BLDNG_CODE_NetworkDesign*.xlsm` template
(41 sheets, VBA macros, one file per school site). See [ROADMAP.md](./ROADMAP.md) for the
full source-workbook analysis and the phased build plan; this is Phase 0.

Stack: **Python/FastAPI + PostgreSQL** backend · **React (Vite) + CSS** frontend, built with
Node tooling.

## What's here (Phase 0)

- `backend/` — FastAPI app with SQLAlchemy models and CRUD API for `Site`, `Room`, `Rack`,
  and the `ReferenceList`/`ReferenceItem` pair that replaces the old `Data Lists` sheet.
  Alembic migrations, plus an `xlsm` importer (`app/importer/xlsm_importer.py`) that pulls
  reference data and site identity out of an existing site workbook.
- `frontend/` — React SPA: site list/create, site detail with rooms/racks, and a
  `ReferenceSelect` dropdown component backed live by the reference-data API (the direct
  replacement for a hardcoded `Data Lists` column).
- `docker-compose.yml` — Postgres + backend for local dev.

Both sides are tested: `cd backend && pytest` (10 tests, including an importer test against
a synthetic fixture) and `cd frontend && npm run build`. The importer was also run against
the real uploaded template and correctly (a) pulled in 62 reference lists / hundreds of
items, and (b) refused to import site identity from it, since that particular file is the
blank master template (no `School Information` values), not a filled-in site.

## Running locally

### With Docker (recommended)

```sh
docker compose up --build
```

Then, in a separate shell, run migrations and start the frontend:

```sh
cd backend && alembic upgrade head   # if not already run by the container
cd frontend && npm install && npm run dev
```

Frontend: http://localhost:5173 · API: http://localhost:8000

### Without Docker

Backend (needs a Postgres instance reachable at `NDP_DATABASE_URL`, or point it at SQLite
for a quick spin: `export NDP_DATABASE_URL=sqlite:///./dev.db`):

```sh
cd backend
pip install -r requirements.txt
alembic upgrade head   # Postgres only -- SQLite: python -c "from app import models; from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
uvicorn app.main:app --reload
```

Frontend:

```sh
cd frontend
npm install
npm run dev
```

### Importing an existing site workbook

```sh
cd backend
python scripts/import_xlsm.py path/to/site.xlsm --name "PS 273" --district 27
# or, to pull in reference data only:
python scripts/import_xlsm.py path/to/site.xlsm --reference-only
```

## Notes on what was and wasn't verified

- `docker-compose.yml` / `Dockerfile` follow standard FastAPI+Postgres patterns but weren't
  build-tested in this environment (no Docker daemon available here) — please confirm on
  first run.
- The `xlsm` importer's `School Information` cell mapping (`F4`/`F5` for building code/rack
  ID) was confirmed by grepping the workbook's own cross-sheet formulas, which are the only
  two School Information cells referenced anywhere else in the template. The other fields
  visible in that sheet (Street Address, DOE FPM Name, Checkout Status, Student Pop.,
  Multi-School Status) aren't referenced elsewhere, so their column couldn't be verified the
  same way — add them to `SCHOOL_INFO_FIELDS` in `xlsm_importer.py` once checked against a
  filled-in site file, rather than guessed.
