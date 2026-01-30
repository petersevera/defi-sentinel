from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query

from rag.index import RagConfig, query_index

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


def _load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_value(key: str, env_file: Dict[str, str], default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key) or env_file.get(key, default)


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


def _count_by(items: Iterable[dict], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        value = str(item.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _top_anomalies(items: List[dict], limit: int) -> List[dict]:
    def _score(item: dict) -> Tuple[float, int]:
        ratio = float(item.get("surge_ratio") or 0.0)
        count_1h = int(item.get("count_1h") or 0)
        return (ratio, count_1h)

    ranked = sorted(items, key=_score, reverse=True)
    return ranked[:limit]


@app.get("/brief")
def brief(limit: int = Query(default=5, ge=1, le=20)) -> dict:
    path = FEATURES_DIR / "anomalies.jsonl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="anomalies.jsonl not found")
    items = _load_jsonl(path)
    return {
        "total_anomalies": len(items),
        "by_protocol": _count_by(items, "protocol"),
        "by_kind": _count_by(items, "kind"),
        "top_anomalies": _top_anomalies(items, limit),
    }


@app.get("/rag/query")
def rag_query(
    q: str = Query(..., min_length=3),
    top_k: int = Query(default=5, ge=1, le=20),
) -> dict:
    env_file = _load_env_file(REPO_ROOT / ".env")
    persist_dir = Path(_env_value("CHROMA_PERSIST_DIR", env_file, "data/chroma"))
    collection = _env_value("CHROMA_COLLECTION", env_file, "defi_sentinel")
    model = _env_value(
        "EMBEDDING_MODEL",
        env_file,
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    if not persist_dir.exists():
        raise HTTPException(status_code=404, detail="Chroma index not found")

    config = RagConfig(
        persist_dir=persist_dir,
        collection_name=collection,
        embedding_model=model,
    )
    return query_index(config, q, top_k=top_k)
