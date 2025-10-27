from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AssetHolding:
    """
    Describes an asset held by an account.

    Definition:
    data/basics/userBalance.go : AssetHolding
    """

    amount: int = field(
        metadata=wire("amount"),
    )
    asset_id: int = field(
        metadata=wire("asset-id"),
    )
    is_frozen: bool = field(
        metadata=wire("is-frozen"),
    )
