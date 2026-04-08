# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TransactionAssetFreeze:
    """
    Fields for an asset freeze transaction.

    Definition:
    data/transactions/asset.go : AssetFreezeTxnFields
    """

    address: str = field(
        default="",
        metadata=wire("address"),
    )
    asset_id: int = field(
        default=0,
        metadata=wire("asset-id"),
    )
    new_freeze_status: bool = field(
        default=False,
        metadata=wire("new-freeze-status"),
    )
