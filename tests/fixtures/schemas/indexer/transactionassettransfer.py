from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TransactionAssetTransferSchema(BaseModel):
    """Fields for an asset transfer transaction.

    Definition:
    data/transactions/asset.go : AssetTransferTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    amount: int = Field(default=None, alias="amount")
    asset_id: int = Field(default=None, alias="asset-id")
    close_amount: int | None = Field(default=None, alias="close-amount")
    close_to: str | None = Field(default=None, alias="close-to")
    receiver: str = Field(default=None, alias="receiver")
    sender: str | None = Field(default=None, alias="sender")
