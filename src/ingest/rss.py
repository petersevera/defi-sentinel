from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable, List, Optional

import feedparser

from normalize.schema import Event


@dataclass(frozen=True)
class RssFeed:
    url: str
    protocol: str
    kind: str


DEFAULT_FEEDS: List[RssFeed] = [
    RssFeed(url="https://governance.aave.com/latest.rss", protocol="aave_v3", kind="governance"),
    RssFeed(url="https://gov.uniswap.org/latest.rss", protocol="uniswap_v3", kind="governance"),
    RssFeed(url="https://blog.openzeppelin.com/rss", protocol="general", kind="advisory"),
    RssFeed(url="https://blog.trailofbits.com/feed/", protocol="general", kind="advisory"),
    RssFeed(url="https://medium.com/feed/immunefi", protocol="general", kind="advisory"),
]


def _parse_datetime(value: Optional[str]) -> datetime:
    if value:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except (TypeError, ValueError):
            pass
    return datetime.now(timezone.utc)


def _slugify(text: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())


def _event_id(protocol: str, kind: str, entry_id: str) -> str:
    slug = _slugify(entry_id)
    if not slug:
        slug = "unknown"
    return f"offchain:{protocol}:{kind}:{slug}"


def _entries(feed_url: str) -> Iterable[dict]:
    parsed = feedparser.parse(feed_url)
    return parsed.entries or []


def fetch_feed(feed: RssFeed) -> List[Event]:
    events: List[Event] = []
    ingest_time = datetime.now(timezone.utc)
    for entry in _entries(feed.url):
        title = entry.get("title", "")
        summary = entry.get("summary", None)
        source_url = entry.get("link", None)
        entry_id = entry.get("id") or source_url or title
        event_time = _parse_datetime(entry.get("published") or entry.get("updated"))
        events.append(
            Event(
                event_id=_event_id(feed.protocol, feed.kind, entry_id),
                source="offchain",
                kind=feed.kind,
                protocol=feed.protocol,
                event_time=event_time,
                ingest_time=ingest_time,
                severity="low" if feed.kind == "governance" else "medium",
                title=title,
                summary=summary,
                source_url=source_url,
                entities=[],
                tags=[feed.kind, "rss"],
                raw={
                    "feed_url": feed.url,
                    "entry_id": entry.get("id"),
                    "published": entry.get("published"),
                },
            )
        )
    return events


def fetch_all(feeds: Iterable[RssFeed] = DEFAULT_FEEDS) -> List[Event]:
    events: List[Event] = []
    seen = set()
    for feed in feeds:
        for event in fetch_feed(feed):
            if event.event_id in seen:
                continue
            seen.add(event.event_id)
            events.append(event)
    return events
