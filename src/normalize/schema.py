from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

Protocol = Literal["aave_v3", "uniswap_v3", "general"]
Source = Literal["onchain", "offchain"]
Kind = Literal["protocol_event", "governance", "advisory"]
Severity = Literal["info", "low", "medium", "high", "critical"]
Chain = Literal["ethereum"]


class Event(BaseModel):
    schema_version: str = Field(default="0.1")
    event_id: str = Field(min_length=8)
    source: Source
    kind: Kind
    protocol: Protocol
    chain: Optional[Chain] = None
    event_time: datetime
    ingest_time: Optional[datetime] = None
    severity: Severity = "info"
    title: str
    summary: Optional[str] = None
    source_url: Optional[str] = None
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    log_index: Optional[int] = None
    entities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_time", "ingest_time")
    @classmethod
    def _tz_aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("timestamp must be timezone-aware")
        return value

    @field_validator("tx_hash")
    @classmethod
    def _tx_hash_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value.startswith("0x") or len(value) != 66:
            raise ValueError("tx_hash must be 0x + 64 hex chars")
        return value

    @model_validator(mode="after")
    def _cross_fields(self) -> "Event":
        if self.source == "onchain":
            if self.chain is None:
                raise ValueError("chain is required for onchain events")
            if self.tx_hash is None or self.block_number is None:
                raise ValueError("tx_hash and block_number are required for onchain events")
            if self.source_url is not None:
                raise ValueError("source_url must be empty for onchain events")
            if self.kind != "protocol_event":
                raise ValueError("onchain events must use kind=protocol_event")
        if self.source == "offchain":
            if self.source_url is None:
                raise ValueError("source_url is required for offchain events")
            if self.chain is not None:
                raise ValueError("chain must be empty for offchain events")
            if self.tx_hash is not None or self.block_number is not None or self.log_index is not None:
                raise ValueError("tx_hash, block_number, log_index must be empty for offchain events")
        return self
