# Feature Store & Anomalies

## What it does
Builds rolling-count features over the canonical event stream and flags simple
surge anomalies. Outputs are stored in DuckDB + Parquet for easy inspection.

## Inputs
- `data/ingest/*.jsonl` (RSS + on-chain ingestion outputs)
- `data/fixtures/*.jsonl` (optional, used if ingest data missing)

## Outputs
- `data/feature_store.duckdb`
- `data/features/feature_snapshot.parquet`
- `data/features/feature_snapshot.jsonl`
- `data/features/anomalies.jsonl`

## Anomaly rule (MVP)
A row is flagged when:
- `count_1h >= 3` AND
- `surge_ratio >= 4.0`, where
  `surge_ratio = (count_1h + 1) / (count_24h/24 + 1)`

This is a conservative, explainable rule intended for a demo. It can be
replaced later with more advanced statistics or ML.

## Run
- `pip install -r requirements.txt`
- `python scripts/build_features.py`

