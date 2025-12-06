# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._asset_holding import AssetHolding
from ._asset_params import AssetParams


@dataclass(slots=True)
class AccountAssetResponse:
    round_: int = field(
        default=0,
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
