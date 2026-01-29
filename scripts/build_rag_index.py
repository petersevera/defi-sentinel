#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag.index import RagConfig, build_index

DATA_DIR = REPO_ROOT / "data"
INGEST_DIR = DATA_DIR / "ingest"
FIXTURES_DIR = DATA_DIR / "fixtures"


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_value(key: str, env_file: dict[str, str], default: str | None = None) -> str | None:
    return os.getenv(key) or env_file.get(key, default)


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _gather_inputs() -> list[Path]:
    paths: list[Path] = []
    if INGEST_DIR.exists():
        paths.extend(sorted(INGEST_DIR.glob("*.jsonl")))
    if paths:
        return paths
    if FIXTURES_DIR.exists():
        paths.extend(sorted(FIXTURES_DIR.glob("*.jsonl")))
    return paths


def main() -> int:
    env_file = _load_env_file(Path(".env"))
    persist_dir = Path(_env_value("CHROMA_PERSIST_DIR", env_file, "data/chroma"))
    collection = _env_value("CHROMA_COLLECTION", env_file, "defi_sentinel")
    model = _env_value(
        "EMBEDDING_MODEL",
        env_file,
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    max_chars = _parse_int(_env_value("RAG_MAX_CHARS", env_file), 1200)
    batch_size = _parse_int(_env_value("RAG_BATCH_SIZE", env_file), 128)

    inputs = _gather_inputs()
    if not inputs:
        print("No input events found in data/ingest or data/fixtures.")
        return 1

    config = RagConfig(
        persist_dir=persist_dir,
        collection_name=collection,
        embedding_model=model,
        max_chars=max_chars,
        batch_size=batch_size,
    )

    total = build_index(config, inputs)
    print(f"indexed {total} chunks into {persist_dir} ({collection})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
