# On-chain Ingestion

## What it does
Fetches Ethereum logs from configured protocol addresses and normalizes them into
canonical events.

## Requirements
- `ALCHEMY_API_KEY` in `.env` or environment.
- Optional addresses for streams:
  - `AAVE_V3_POOL_ADDRESS` (if unset, Aave stream is skipped)
  - `UNISWAP_V3_WETH_USDC_POOL` (defaults to WETH/USDC 0.05% pool)

## Run
- `pip install -r requirements.txt`
- `python scripts/ingest_onchain.py`

Output is written to `data/ingest/onchain_events.jsonl`.

## Block range
- Default: last `ONCHAIN_LOOKBACK_BLOCKS` blocks.
- Override with `START_BLOCK` / `END_BLOCK` in `.env`.
- Note: Alchemy free tier allows a max 10-block range for `eth_getLogs`.
