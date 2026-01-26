# Configuration

## Required
- `ALCHEMY_API_KEY` - Alchemy API key for Ethereum mainnet.

## Optional
- `ALCHEMY_RPC_URL` - Full RPC URL. If unset, build as
  `https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}`.
- `RSS_FEEDS` - Override RSS sources (see docs/INGEST_RSS.md).
- `AAVE_V3_POOL_ADDRESS` - Enable Aave v3 log ingestion (Pool contract address).
- `UNISWAP_V3_WETH_USDC_POOL` - Pool address for Uniswap v3 swap logs.
- `ONCHAIN_LOOKBACK_BLOCKS` - How many blocks back to scan when START/END not set (default 10).
- `START_BLOCK` - Optional explicit start block for on-chain ingestion.
- `END_BLOCK` - Optional explicit end block for on-chain ingestion.

## Example
Copy `.env.example` to `.env` and fill in your key.
