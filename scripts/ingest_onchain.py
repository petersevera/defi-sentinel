#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from web3 import Web3

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ingest.onchain import DEFAULT_UNISWAP_V3_POOL, build_default_streams, fetch_stream_events


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_value(key: str, env_file: dict[str, str], default: str | None = None) -> str | None:
    return os.getenv(key) or env_file.get(key, default)


def _parse_int(value: str | None, name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def main() -> int:
    env_file = _load_env_file(Path(".env"))
    rpc_url = _env_value("ALCHEMY_RPC_URL", env_file)
    if not rpc_url:
        api_key = _env_value("ALCHEMY_API_KEY", env_file)
        if not api_key:
            print("ALCHEMY_API_KEY is required", file=sys.stderr)
            return 1
        rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("RPC connection failed", file=sys.stderr)
        return 1

    start_block = _parse_int(_env_value("START_BLOCK", env_file), "START_BLOCK")
    end_block = _parse_int(_env_value("END_BLOCK", env_file), "END_BLOCK")
    lookback = _parse_int(_env_value("ONCHAIN_LOOKBACK_BLOCKS", env_file, "10"), "ONCHAIN_LOOKBACK_BLOCKS")
    if lookback is None:
        lookback = 10
    if lookback < 1:
        print("ONCHAIN_LOOKBACK_BLOCKS must be >= 1", file=sys.stderr)
        return 1

    latest_block = w3.eth.block_number
    if end_block is None:
        end_block = latest_block
    if start_block is None:
        start_block = max(0, end_block - (lookback - 1))

    if start_block > end_block:
        print("START_BLOCK must be <= END_BLOCK", file=sys.stderr)
        return 1

    aave_pool = _env_value("AAVE_V3_POOL_ADDRESS", env_file)
    uniswap_pool = _env_value("UNISWAP_V3_WETH_USDC_POOL", env_file, DEFAULT_UNISWAP_V3_POOL)
    streams = build_default_streams(aave_pool, uniswap_pool)
    if not streams:
        print("No on-chain streams configured.", file=sys.stderr)
        return 1

    events = []
    seen = set()
    for stream in streams:
        for event in fetch_stream_events(w3, stream, start_block, end_block):
            if event.event_id in seen:
                continue
            seen.add(event.event_id)
            events.append(event)

    output_dir = Path("data") / "ingest"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "onchain_events.jsonl"

    with output_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event.model_dump(mode="json")) + "\n")

    print(
        f"wrote {len(events)} events to {output_path} "
        f"(blocks {start_block}-{end_block})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
