from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence

import json

import duckdb

CANONICAL_KEYS = [
    "schema_version",
    "event_id",
    "source",
    "kind",
    "protocol",
    "chain",
    "event_time",
    "ingest_time",
    "severity",
    "title",
    "summary",
    "source_url",
    "tx_hash",
    "block_number",
    "log_index",
    "entities",
    "tags",
    "raw",
]

DEFAULTS = {
    "schema_version": "0.1",
    "chain": None,
    "ingest_time": None,
    "severity": "info",
    "summary": None,
    "source_url": None,
    "tx_hash": None,
    "block_number": None,
    "log_index": None,
    "entities": [],
    "tags": [],
    "raw": {},
}


@dataclass(frozen=True)
class FeatureRow:
    protocol: str
    source: str
    kind: str
    count_1h: int
    count_24h: int
    count_7d: int
    expected_1h: float
    surge_ratio: float
    as_of: datetime


def _build_union_query(paths: Sequence[Path]) -> tuple[str, list[str]]:
    selects = []
    params: list[str] = []
    for path in paths:
        selects.append("SELECT * FROM read_json_auto(?)")
        params.append(str(path))
    return " UNION ALL ".join(selects), params


def normalize_events(inputs: Sequence[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out_handle:
        for path in inputs:
            with path.open("r", encoding="utf-8") as in_handle:
                for line in in_handle:
                    text = line.strip()
                    if not text:
                        continue
                    payload = json.loads(text)
                    for key in CANONICAL_KEYS:
                        if key not in payload:
                            payload[key] = DEFAULTS.get(key)
                    if payload.get("entities") is None:
                        payload["entities"] = []
                    if payload.get("tags") is None:
                        payload["tags"] = []
                    if payload.get("raw") is None:
                        payload["raw"] = {}
                    out_handle.write(json.dumps(payload) + "\n")


def load_events(conn: duckdb.DuckDBPyConnection, paths: Sequence[Path]) -> None:
    if not paths:
        raise ValueError("no input files provided")
    union_sql, params = _build_union_query(paths)
    sql = (
        "CREATE OR REPLACE TABLE events AS "
        "SELECT *, CAST(event_time AS TIMESTAMP) AS event_time_ts "
        f"FROM ({union_sql})"
    )
    conn.execute(sql, params)


def compute_features(conn: duckdb.DuckDBPyConnection) -> List[FeatureRow]:
    as_of = conn.execute("SELECT max(event_time_ts) FROM events").fetchone()[0]
    if as_of is None:
        return []

    as_of_literal = as_of.isoformat(sep=" ", timespec="seconds")
    conn.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW feature_snapshot AS
        WITH agg AS (
            SELECT
                protocol,
                source,
                kind,
                SUM(CASE WHEN event_time_ts >= TIMESTAMP '{as_of_literal}' - INTERVAL '1 hour' THEN 1 ELSE 0 END) AS count_1h,
                SUM(CASE WHEN event_time_ts >= TIMESTAMP '{as_of_literal}' - INTERVAL '24 hours' THEN 1 ELSE 0 END) AS count_24h,
                SUM(CASE WHEN event_time_ts >= TIMESTAMP '{as_of_literal}' - INTERVAL '7 days' THEN 1 ELSE 0 END) AS count_7d
            FROM events
            GROUP BY 1, 2, 3
        )
        SELECT
            protocol,
            source,
            kind,
            count_1h,
            count_24h,
            count_7d,
            (count_24h / 24.0) AS expected_1h,
            (count_1h + 1.0) / (count_24h / 24.0 + 1.0) AS surge_ratio,
            TIMESTAMP '{as_of_literal}' AS as_of
        FROM agg
        """
    )

    rows = conn.execute(
        """
        SELECT protocol, source, kind, count_1h, count_24h, count_7d, expected_1h, surge_ratio, as_of
        FROM feature_snapshot
        """
    ).fetchall()

    results: List[FeatureRow] = []
    for row in rows:
        results.append(FeatureRow(*row))
    return results


def find_anomalies(rows: Iterable[FeatureRow]) -> List[FeatureRow]:
    anomalies: List[FeatureRow] = []
    for row in rows:
        if row.count_1h >= 3 and row.surge_ratio >= 4.0:
            anomalies.append(row)
    return anomalies


def write_outputs(
    conn: duckdb.DuckDBPyConnection,
    feature_rows: Sequence[FeatureRow],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = out_dir / "feature_snapshot.parquet"
    json_path = out_dir / "feature_snapshot.jsonl"

    conn.execute(
        f"COPY feature_snapshot TO '{parquet_path.as_posix()}' (FORMAT 'parquet')"
    )

    with json_path.open("w", encoding="utf-8") as handle:
        for row in feature_rows:
            handle.write(
                "{"
                f"\"protocol\":\"{row.protocol}\","
                f"\"source\":\"{row.source}\","
                f"\"kind\":\"{row.kind}\","
                f"\"count_1h\":{row.count_1h},"
                f"\"count_24h\":{row.count_24h},"
                f"\"count_7d\":{row.count_7d},"
                f"\"expected_1h\":{row.expected_1h},"
                f"\"surge_ratio\":{row.surge_ratio},"
                f"\"as_of\":\"{row.as_of.isoformat()}\""
                "}\n"
            )


def write_anomalies(rows: Sequence[FeatureRow], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "anomalies.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                "{"
                f"\"protocol\":\"{row.protocol}\","
                f"\"source\":\"{row.source}\","
                f"\"kind\":\"{row.kind}\","
                f"\"count_1h\":{row.count_1h},"
                f"\"count_24h\":{row.count_24h},"
                f"\"count_7d\":{row.count_7d},"
                f"\"expected_1h\":{row.expected_1h},"
                f"\"surge_ratio\":{row.surge_ratio},"
                f"\"as_of\":\"{row.as_of.isoformat()}\""
                "}\n"
            )
    return path


def open_store(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(database=str(db_path))
