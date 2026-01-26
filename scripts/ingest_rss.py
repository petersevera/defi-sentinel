#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ingest.rss import DEFAULT_FEEDS, RssFeed, fetch_all


def _parse_custom_feeds(raw: str | None) -> list[RssFeed]:
    if not raw:
        return []
    feeds: list[RssFeed] = []
    for line in raw.split(","):
        text = line.strip()
        if not text:
            continue
        parts = [part.strip() for part in text.split("|")]
        if len(parts) != 3:
            raise ValueError("custom feeds must be url|protocol|kind")
        feeds.append(RssFeed(url=parts[0], protocol=parts[1], kind=parts[2]))
    return feeds


def main() -> int:
    env = Path(".env")
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "RSS_FEEDS":
                custom = _parse_custom_feeds(value.strip())
                feeds = custom if custom else DEFAULT_FEEDS
                break
        else:
            feeds = DEFAULT_FEEDS
    else:
        feeds = DEFAULT_FEEDS

    events = fetch_all(feeds)
    output_dir = Path("data") / "ingest"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "rss_events.jsonl"

    with output_path.open("w", encoding="utf-8") as handle:
        for event in events:
            payload = event.model_dump(mode="json")
            handle.write(json.dumps(payload) + "\n")

    print(f"wrote {len(events)} events to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
