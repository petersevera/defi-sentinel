# Architecture

## System flow

[Data Sources]
  - On-chain events (Ethereum mainnet, Aave v3, Uniswap v3)
  - Off-chain signals (RSS governance, security advisories)
        |
        v
[Ingest]
  - Pull connectors (Alchemy RPC, RSS)
  - Backfill + incremental fetch
        |
        v
[Normalize]
  - Canonical event schema
  - Event-time ordering + dedupe
  - Validation + enrichment
        |
        v
[Feature Store]
  - Rolling windows (1h, 24h, 7d)
  - Risk indicators (volume spikes, liquidation bursts)
  - DuckDB + Parquet snapshots
        |
        v
[Vector Index]
  - Embeddings for RAG
  - Traceable sources + citations
  - Chroma (local)
        |
        v
[RAG + Agent]
  - Retrieval for context
  - LangChain retrieval + LangGraph workflows
  - Briefing agent (daily summary)
  - Alert agent (anomaly triggers)
        |
        v
[Outputs]
  - FastAPI (REST)
  - Typer CLI
  - Markdown briefs

## MVP targets
- Chain: Ethereum mainnet
- Protocols: Aave v3, Uniswap v3
- On-chain access: Alchemy RPC
- Off-chain RSS:
  - https://governance.aave.com/latest.rss
  - https://gov.uniswap.org/latest.rss
  - https://blog.openzeppelin.com/rss
  - https://blog.trailofbits.com/feed/
  - https://medium.com/feed/immunefi

## Core design decisions
- Event-time semantics to avoid false alerts from late data.
- Idempotent ingest to support backfills and replays.
- Source traceability to keep LLM outputs auditable.
- Local-first stack to keep onboarding simple.

## C++ accelerator (phase 2)
- Stream aggregation for high-rate events (rolling stats, top-K, histograms).
- Python bindings via pybind11 for seamless integration.

## Observability
- Structured logging with correlation ids.
- Metrics: ingestion lag, dedupe rate, alert count.
