# RSS Ingestion

## Default feeds
- Aave governance: https://governance.aave.com/latest.rss
- Uniswap governance: https://gov.uniswap.org/latest.rss
- OpenZeppelin: https://blog.openzeppelin.com/rss
- Trail of Bits: https://blog.trailofbits.com/feed/
- Immunefi: https://medium.com/feed/immunefi

## Run
- `pip install -r requirements.txt`
- `python scripts/ingest_rss.py`

Output is written to `data/ingest/rss_events.jsonl`.

## Custom feeds
You can override feeds by setting `RSS_FEEDS` in `.env` as a comma-separated list of
`url|protocol|kind` entries.

Example:
RSS_FEEDS=https://example.com/rss|general|advisory,https://gov.example.org/rss|aave_v3|governance

