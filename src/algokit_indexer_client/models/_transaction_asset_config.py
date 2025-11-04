# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._asset_params import AssetParams


@dataclass(slots=True)
class TransactionAssetConfig:
    """
    Fields for asset allocation, re-configuration, and destruction.


    A zero value for asset-id indicates asset creation.
    A zero value for the params indicates asset destruction.

    Definition:
    data/transactions/asset.go : AssetConfigTxnFields
    """

    asset_id: int | None = field(
        default=None,
        metadata=wire("asset-id"),
    )
    params: AssetParams | None = field(
        default=None,
        metadata=nested("params", lambda: AssetParams),
    )
