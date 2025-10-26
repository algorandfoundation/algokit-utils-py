from __future__ import annotations

from dataclasses import dataclass, field

from algokit_transact.codec.serde import addr, wire


@dataclass(slots=True, frozen=True)
class AssetTransferTransactionFields:
    asset_id: int = field(metadata=wire("xaid"))
    receiver: str = field(metadata=addr("arcv"))
    amount: int = field(default=0, metadata=wire("aamt"))
    close_remainder_to: str | None = field(default=None, metadata=addr("aclose", omit_if_none=True))
    asset_sender: str | None = field(default=None, metadata=addr("asnd", omit_if_none=True))
