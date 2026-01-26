# Configuration

## Required
- `ALCHEMY_API_KEY` - Alchemy API key for Ethereum mainnet.

## Optional
- `ALCHEMY_RPC_URL` - Full RPC URL. If unset, build as
  `https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}`.
- `RSS_FEEDS` - Override RSS sources (see docs/INGEST_RSS.md).

## Example
Copy `.env.example` to `.env` and fill in your key.
