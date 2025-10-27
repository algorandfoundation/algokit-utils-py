from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .asset_holding import AssetHolding
from .asset_params import AssetParams


@dataclass(slots=True)
class AccountAssetInformationResponseModel:
    round_: int = field(
        metadata=wire("round"),
    )
    asset_holding: AssetHolding | None = field(
        default=None,
        metadata=nested("asset-holding", lambda: AssetHolding),
    )
    created_asset: AssetParams | None = field(
        default=None,
        metadata=nested("created-asset", lambda: AssetParams),
    )
