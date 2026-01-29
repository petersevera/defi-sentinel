# API

Minimal read-only API for inspecting events and feature outputs.

## Run
- `pip install -r requirements.txt`
- `python scripts/run_api.py`

## Endpoints
- `GET /health` -> {"status": "ok"}
- `GET /events` -> list of events (from `data/ingest` or fixtures)
  - Query params: `source`, `kind`, `protocol`, `limit`
- `GET /features/latest` -> latest feature snapshot
  - Query params: `limit`
- `GET /anomalies` -> anomaly rows
- `GET /brief` -> summary of anomalies
  - Query params: `limit` (top anomalies)

Notes:
- Endpoints return 404 if the expected data files do not exist.
- The API reads local JSONL files and does not require a database.
