from pydantic import BaseModel, ConfigDict, Field


class TransactionAssetTransferSchema(BaseModel):
    """Fields for an asset transfer transaction.

    Definition:
    data/transactions/asset.go : AssetTransferTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(alias="amount")
    asset_id: int = Field(alias="asset-id")
    close_amount: int | None = Field(default=None, alias="close-amount")
    close_to: str | None = Field(default=None, alias="close-to")
    receiver: str = Field(alias="receiver")
    sender: str | None = Field(default=None, alias="sender")
