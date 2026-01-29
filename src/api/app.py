from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from fastapi import FastAPI, HTTPException, Query

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
INGEST_DIR = DATA_DIR / "ingest"
FIXTURES_DIR = DATA_DIR / "fixtures"
FEATURES_DIR = DATA_DIR / "features"

app = FastAPI(title="DeFi Sentinel API", version="0.1")


def _iter_event_files() -> List[Path]:
    ingest_files = sorted(INGEST_DIR.glob("*.jsonl")) if INGEST_DIR.exists() else []
    if ingest_files:
        return ingest_files
    return sorted(FIXTURES_DIR.glob("*.jsonl")) if FIXTURES_DIR.exists() else []


def _load_jsonl(path: Path) -> List[dict]:
    items: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            items.append(json.loads(text))
    return items


def _filter_events(
    events: Iterable[dict],
    source: Optional[str],
    kind: Optional[str],
    protocol: Optional[str],
    limit: int,
) -> List[dict]:
    results: List[dict] = []
    for event in events:
        if source and event.get("source") != source:
            continue
        if kind and event.get("kind") != kind:
            continue
        if protocol and event.get("protocol") != protocol:
            continue
        results.append(event)
        if len(results) >= limit:
            break
    return results


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/events")
def list_events(
    source: Optional[str] = None,
    kind: Optional[str] = None,
    protocol: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
) -> List[dict]:
    files = _iter_event_files()
    if not files:
        raise HTTPException(status_code=404, detail="No event files found")

    results: List[dict] = []
    for path in files:
        events = _load_jsonl(path)
        results.extend(_filter_events(events, source, kind, protocol, limit - len(results)))
        if len(results) >= limit:
            break
    return results


@app.get("/features/latest")
def latest_features(limit: int = Query(default=200, ge=1, le=1000)) -> List[dict]:
    path = FEATURES_DIR / "feature_snapshot.jsonl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="feature_snapshot.jsonl not found")
    items = _load_jsonl(path)
    return items[:limit]


@app.get("/anomalies")
def anomalies() -> List[dict]:
    path = FEATURES_DIR / "anomalies.jsonl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="anomalies.jsonl not found")
    return _load_jsonl(path)
