from __future__ import annotations

import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

# Chroma requires sqlite3 >= 3.35.0; fall back to pysqlite3-binary if needed.
if sqlite3.sqlite_version_info < (3, 35, 0):
    try:
        import pysqlite3  # type: ignore

        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        pass

import chromadb
from chromadb.utils import embedding_functions


@dataclass(frozen=True)
class RagConfig:
    persist_dir: Path
    collection_name: str
    embedding_model: str
    max_chars: int = 1200
    batch_size: int = 128


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _build_text(event: dict) -> str:
    title = event.get("title") or ""
    summary = event.get("summary") or ""
    source_url = event.get("source_url") or ""
    parts = [title, summary, source_url]
    return "\n".join(part for part in parts if part)


def _chunk_text(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end])
        start = end
    return chunks


def _iter_jsonl(paths: Sequence[Path]) -> Iterable[dict]:
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                yield json.loads(text)


def _event_metadata(event: dict) -> Dict[str, str]:
    metadata = {
        "event_id": str(event.get("event_id", "")),
        "source": str(event.get("source", "")),
        "kind": str(event.get("kind", "")),
        "protocol": str(event.get("protocol", "")),
        "event_time": str(event.get("event_time", "")),
    }
    if event.get("source_url"):
        metadata["source_url"] = str(event.get("source_url"))
    if event.get("tx_hash"):
        metadata["tx_hash"] = str(event.get("tx_hash"))
    return metadata


def iter_documents(paths: Sequence[Path], max_chars: int) -> Iterable[Tuple[str, str, Dict[str, str]]]:
    for event in _iter_jsonl(paths):
        base_text = _build_text(event)
        if not base_text:
            continue
        text = _strip_html(base_text)
        chunks = _chunk_text(text, max_chars)
        base_id = str(event.get("event_id", ""))
        metadata = _event_metadata(event)
        total = len(chunks)
        for idx, chunk in enumerate(chunks):
            doc_id = f"{base_id}:{idx}" if total > 1 else base_id
            meta = dict(metadata)
            meta["chunk"] = str(idx)
            meta["chunks"] = str(total)
            yield doc_id, chunk, meta


def build_index(config: RagConfig, paths: Sequence[Path]) -> int:
    config.persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(config.persist_dir))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.embedding_model
    )
    collection = client.get_or_create_collection(
        name=config.collection_name,
        embedding_function=embed_fn,
        metadata={"description": "DeFi Sentinel RAG index"},
    )

    ids: List[str] = []
    docs: List[str] = []
    metas: List[Dict[str, str]] = []
    total = 0

    for doc_id, text, meta in iter_documents(paths, config.max_chars):
        ids.append(doc_id)
        docs.append(text)
        metas.append(meta)
        if len(ids) >= config.batch_size:
            collection.upsert(ids=ids, documents=docs, metadatas=metas)
            total += len(ids)
            ids, docs, metas = [], [], []

    if ids:
        collection.upsert(ids=ids, documents=docs, metadatas=metas)
        total += len(ids)

    return total


def query_index(
    config: RagConfig,
    query: str,
    top_k: int = 5,
) -> dict:
    client = chromadb.PersistentClient(path=str(config.persist_dir))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.embedding_model
    )
    collection = client.get_or_create_collection(
        name=config.collection_name,
        embedding_function=embed_fn,
    )
    return collection.query(query_texts=[query], n_results=top_k)
