# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested

from ._asset_holding import AssetHolding
from ._asset_params import AssetParams


@dataclass(slots=True)
class AccountAssetHolding:
    """
    AccountAssetHolding describes the account's asset holding and asset parameters (if
    either exist) for a specific asset ID.
    """

    asset_holding: AssetHolding = field(
        metadata=nested("asset-holding", lambda: AssetHolding, required=True),
    )
    asset_params: AssetParams | None = field(
        default=None,
        metadata=nested("asset-params", lambda: AssetParams),
    )
