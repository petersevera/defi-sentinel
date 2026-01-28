#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from features.store import (
    compute_features,
    find_anomalies,
    load_events,
    normalize_events,
    open_store,
    write_anomalies,
    write_outputs,
)

DATA_DIR = REPO_ROOT / "data"
INGEST_DIR = DATA_DIR / "ingest"
FIXTURES_DIR = DATA_DIR / "fixtures"
FEATURES_DIR = DATA_DIR / "features"
DB_PATH = DATA_DIR / "feature_store.duckdb"
NORMALIZED_PATH = FEATURES_DIR / "_events_normalized.jsonl"


def _gather_inputs() -> list[Path]:
    paths: list[Path] = []
    if INGEST_DIR.exists():
        paths.extend(sorted(INGEST_DIR.glob("*.jsonl")))
    if FIXTURES_DIR.exists():
        paths.extend(sorted(FIXTURES_DIR.glob("*.jsonl")))
    return paths


def main() -> int:
    inputs = _gather_inputs()
    if not inputs:
        print("No input events found in data/ingest or data/fixtures.")
        return 1

    conn = open_store(DB_PATH)
    try:
        normalize_events(inputs, NORMALIZED_PATH)
        load_events(conn, [NORMALIZED_PATH])
        features = compute_features(conn)
        if not features:
            print("No events to compute features.")
            return 1
        write_outputs(conn, features, FEATURES_DIR)
        anomalies = find_anomalies(features)
        write_anomalies(anomalies, FEATURES_DIR)
        print(
            f"wrote {len(features)} feature rows and {len(anomalies)} anomalies to {FEATURES_DIR}"
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
