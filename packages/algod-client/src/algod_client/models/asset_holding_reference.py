from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AssetHoldingReference:
    """
    References an asset held by an account.
    """

    account: str = field(
        metadata=wire("account"),
    )
    asset: int = field(
        metadata=wire("asset"),
    )
