from __future__ import annotations

from dataclasses import dataclass, field

from algokit_transact.codec.serde import addr, wire


@dataclass(slots=True, frozen=True)
class AssetFreezeTransactionFields:
    asset_id: int = field(metadata=wire("faid"))
    freeze_target: str = field(metadata=addr("fadd"))
    frozen: bool = field(default=False, metadata=wire("afrz"))
