# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TransactionAssetTransfer:
    """
    Fields for an asset transfer transaction.

    Definition:
    data/transactions/asset.go : AssetTransferTxnFields
    """

    amount: int = field(
        default=0,
        metadata=wire("amount"),
    )
    asset_id: int = field(
        default=0,
        metadata=wire("asset-id"),
    )
    receiver: str = field(
        default="",
        metadata=wire("receiver"),
    )
    close_amount: int | None = field(
        default=None,
        metadata=wire("close-amount"),
    )
    close_to: str | None = field(
        default=None,
        metadata=wire("close-to"),
    )
    sender: str | None = field(
        default=None,
        metadata=wire("sender"),
    )
