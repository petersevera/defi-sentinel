from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from web3 import Web3

from normalize.schema import Event

DEFAULT_UNISWAP_V3_POOL = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"
AAVE_LIQUIDATION_SIGNATURE = (
    "LiquidationCall(address,address,address,uint256,uint256,address,bool)"
)
UNISWAP_SWAP_SIGNATURE = "Swap(address,address,int256,int256,uint160,uint128,int24)"


@dataclass(frozen=True)
class OnchainStream:
    name: str
    protocol: str
    address: str
    signature: str
    severity: str = "medium"
    title: str = "On-chain event"
    tags: List[str] = field(default_factory=list)


def build_default_streams(
    aave_pool_address: Optional[str],
    uniswap_pool_address: Optional[str],
) -> List[OnchainStream]:
    streams: List[OnchainStream] = []
    if aave_pool_address:
        streams.append(
            OnchainStream(
                name="aave_v3_liquidation",
                protocol="aave_v3",
                address=aave_pool_address,
                signature=AAVE_LIQUIDATION_SIGNATURE,
                severity="high",
                title="Aave v3 LiquidationCall",
                tags=["liquidation"],
            )
        )
    if uniswap_pool_address:
        streams.append(
            OnchainStream(
                name="uniswap_v3_swap",
                protocol="uniswap_v3",
                address=uniswap_pool_address,
                signature=UNISWAP_SWAP_SIGNATURE,
                severity="medium",
                title="Uniswap v3 Swap",
                tags=["swap"],
            )
        )
    return streams


def _topic0(signature: str) -> str:
    return Web3.to_hex(Web3.keccak(text=signature))


def _block_time(w3: Web3, block_number: int, cache: Dict[int, datetime]) -> datetime:
    if block_number not in cache:
        block = w3.eth.get_block(block_number)
        cache[block_number] = datetime.fromtimestamp(block["timestamp"], timezone.utc)
    return cache[block_number]


def fetch_stream_events(
    w3: Web3,
    stream: OnchainStream,
    from_block: int,
    to_block: int,
) -> List[Event]:
    from_block_hex = hex(from_block)
    to_block_hex = hex(to_block)
    address = Web3.to_checksum_address(stream.address)
    topic0 = _topic0(stream.signature)
    filter_params = {
        "fromBlock": from_block_hex,
        "toBlock": to_block_hex,
        "address": address,
        "topics": [topic0],
    }
    logs = w3.eth.get_logs(filter_params)
    ingest_time = datetime.now(timezone.utc)
    block_cache: Dict[int, datetime] = {}
    events: List[Event] = []

    for log in logs:
        block_number = log["blockNumber"]
        log_index = log["logIndex"]
        tx_hash = Web3.to_hex(log["transactionHash"])
        event_time = _block_time(w3, block_number, block_cache)
        topics = [Web3.to_hex(topic) for topic in log["topics"]]
        events.append(
            Event(
                event_id=(
                    f"onchain:{stream.protocol}:{stream.name}"
                    f":{tx_hash}:{block_number}:{log_index}"
                ),
                source="onchain",
                kind="protocol_event",
                protocol=stream.protocol,
                chain="ethereum",
                event_time=event_time,
                ingest_time=ingest_time,
                severity=stream.severity,
                title=stream.title,
                summary=f"{stream.title} log from {stream.protocol}",
                tx_hash=tx_hash,
                block_number=block_number,
                log_index=log_index,
                entities=[address],
                tags=["onchain", stream.name] + list(stream.tags),
                raw={
                    "address": log["address"],
                    "data": Web3.to_hex(log["data"]),
                    "topics": topics,
                    "topic0": topic0,
                },
            )
        )

    return events
