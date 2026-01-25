#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"

sys.path.insert(0, str(REPO_ROOT / "src"))

from normalize.schema import Event


def _iter_paths(args: list[str]) -> list[Path]:
    if not args:
        if not FIXTURES_DIR.exists():
            return []
        return sorted(FIXTURES_DIR.glob("*.jsonl"))

    paths: list[Path] = []
    for raw in args:
        path = Path(raw)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.jsonl")))
        else:
            paths.append(path)
    return paths


def _validate_file(path: Path) -> tuple[int, int]:
    errors = 0
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            total += 1
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                print(f"{path.name}:{line_no} json error: {exc}")
                errors += 1
                continue
            try:
                Event.model_validate(payload)
            except Exception as exc:
                print(f"{path.name}:{line_no} schema error: {exc}")
                errors += 1
    return total, errors


def main() -> int:
    paths = _iter_paths(sys.argv[1:])
    if not paths:
        print("No fixture files found.")
        return 1

    total_records = 0
    total_errors = 0
    for path in paths:
        count, errors = _validate_file(path)
        total_records += count
        total_errors += errors
        status = "ok" if errors == 0 else "fail"
        print(f"{path.name}: {status} ({count} records)")

    if total_errors:
        print(f"validation failed: {total_errors} errors across {total_records} records")
        return 1

    print(f"validation passed: {total_records} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
