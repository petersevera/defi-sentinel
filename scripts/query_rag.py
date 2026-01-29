#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag.index import RagConfig, query_index


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_value(key: str, env_file: dict[str, str], default: str | None = None) -> str | None:
    return os.getenv(key) or env_file.get(key, default)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/query_rag.py \"your query\"")
        return 1

    query = " ".join(sys.argv[1:])
    env_file = _load_env_file(Path(".env"))
    persist_dir = Path(_env_value("CHROMA_PERSIST_DIR", env_file, "data/chroma"))
    collection = _env_value("CHROMA_COLLECTION", env_file, "defi_sentinel")
    model = _env_value(
        "EMBEDDING_MODEL",
        env_file,
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    config = RagConfig(
        persist_dir=persist_dir,
        collection_name=collection,
        embedding_model=model,
    )
    results = query_index(config, query, top_k=5)
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
