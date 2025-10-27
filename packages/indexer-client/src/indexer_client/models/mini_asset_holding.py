from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class MiniAssetHolding:
    """
    A simplified version of AssetHolding
    """

    address: str = field(
        metadata=wire("address"),
    )
    amount: int = field(
        metadata=wire("amount"),
    )
    is_frozen: bool = field(
        metadata=wire("is-frozen"),
    )
    deleted: bool | None = field(
        default=None,
        metadata=wire("deleted"),
    )
    opted_in_at_round: int | None = field(
        default=None,
        metadata=wire("opted-in-at-round"),
    )
    opted_out_at_round: int | None = field(
        default=None,
        metadata=wire("opted-out-at-round"),
    )
