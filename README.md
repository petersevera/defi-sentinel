# defi-sentinel

DeFi risk and incident monitoring with RAG and agentic workflows.

Goal: a production-grade pipeline that fuses on-chain data and off-chain signals to generate
clear, actionable risk briefs and alerts for DeFi protocols. This showcases end-to-end
skills across data engineering, LLM + RAG, agent orchestration, and low-latency components.

## Quickstart
- Copy `.env.example` to `.env` and fill in `ALCHEMY_API_KEY`.
- Install core dependencies: `pip install -r requirements-core.txt`
- Validate fixtures: `python scripts/validate_fixtures.py`
- Build features: `python scripts/build_features.py`

For RAG indexing, install full dependencies: `pip install -r requirements-rag.txt`.

## MVP scope
- Ingest on-chain events from Ethereum mainnet for Aave v3 and Uniswap v3 via Alchemy RPC.
- Ingest off-chain signals from public RSS feeds (governance, security advisories).
- Normalize all signals into a single event schema with event-time semantics.
- Build a feature store in DuckDB with rolling windows and anomaly flags.
- Index documents into Chroma for RAG queries.
- Run a LangGraph workflow that produces:
  - Daily protocol risk briefs
  - Real-time alert summaries on anomalies
- Expose a read-only FastAPI service and a Typer CLI for queries.

## MVP data sources
- On-chain: Ethereum mainnet via Alchemy RPC.
- Governance RSS:
  - https://governance.aave.com/latest.rss
  - https://gov.uniswap.org/latest.rss
- Security advisories RSS:
  - https://blog.openzeppelin.com/rss
  - https://blog.trailofbits.com/feed/
  - https://medium.com/feed/immunefi

## Configuration
- Required env: `ALCHEMY_API_KEY`
- Optional env: `ALCHEMY_RPC_URL`
- See docs/CONFIG.md for details.

## Phase 0: schema + fixtures + validator
- Fixtures live in `data/fixtures/*.jsonl` (on-chain and off-chain samples).
- Schema is defined in `src/normalize/schema.py`.
- Validate fixtures:
  - `pip install -r requirements-core.txt`
  - `python scripts/validate_fixtures.py`

## Phase 1: RSS ingestion
- Fetch and normalize RSS entries into the canonical event schema.
- Default feeds are in `src/ingest/rss.py`.
- Details: `docs/INGEST_RSS.md`.
- Run:
  - `pip install -r requirements-core.txt`
  - `python scripts/ingest_rss.py`
- Output: `data/ingest/rss_events.jsonl`

## Phase 1: on-chain ingestion
- Fetch and normalize Ethereum logs via Alchemy.
- Details: `docs/INGEST_ONCHAIN.md`.
- Run:
  - `pip install -r requirements-core.txt`
  - `python scripts/ingest_onchain.py`
- Output: `data/ingest/onchain_events.jsonl`

## Phase 2: feature store + anomalies
- Build rolling-count features from ingested events and flag simple surges.
- Details: `docs/FEATURE_STORE.md`.
- Run:
  - `pip install -r requirements-core.txt`
  - `python scripts/build_features.py`
- Outputs: `data/feature_store.duckdb`, `data/features/*`

## Phase 3: read-only API
- FastAPI service that reads local JSONL outputs.
- Details: `docs/API.md`.
- Run:
  - `pip install -r requirements-core.txt`
  - `python scripts/run_api.py`

## Phase 4: RAG index
- Build a Chroma vector index from ingested events for retrieval.
- Details: `docs/RAG.md`.
- Run:
  - `pip install -r requirements-rag.txt`
  - `python scripts/build_rag_index.py`

## Why it matters
- Useful to engineers, analysts, and teams who want transparent, explainable risk context.
- Demonstrates practical LLM + RAG usage with real data pipelines and operational concerns.
- Highlights performance engineering via a C++ aggregation module with Python bindings.

## Architecture (high level)
Data Sources -> Ingest -> Normalize -> Feature Store -> Vector Index -> RAG -> Agent -> Outputs

See docs/ARCHITECTURE.md for more detail.

## Planned repository layout
- src/ingest/        Data connectors (on-chain, RSS, advisories)
- src/normalize/     Schema, validation, event-time handling
- src/features/      Rolling metrics, anomaly detection
- src/rag/           Embeddings, retrieval, prompt tooling
- src/agents/        Briefing and alert workflows
- src/api/           REST API (read-only)
- src/cli/           Local CLI for queries
- src/cpp/           High-throughput aggregations
- tests/             Unit + integration tests
- docs/              Design docs and roadmap

## Tech stack (selected)
- Python 3.11, FastAPI, LangChain, LangGraph, Web3.py
- LLM + embeddings: Llama 3 + BGE (local, via sentence-transformers)
- Vector DB: Chroma (local)
- Storage: DuckDB + Parquet
- C++ core for high-rate aggregations (pybind11)
- Docker, GitHub Actions

## Non-goals for MVP
- No live trading or capital deployment.
- No proprietary data sources required to run locally.
- No UI dashboard in phase 1 (API + CLI only).

## Roadmap
- Phase 0: local fixtures and schema validation
- Phase 1: end-to-end MVP pipeline with API + CLI
- Phase 2: streaming ingestion and C++ accelerator
- Phase 3: optional UI dashboard and multi-chain support
