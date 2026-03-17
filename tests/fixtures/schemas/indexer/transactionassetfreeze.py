from pydantic import BaseModel, ConfigDict, Field


class TransactionAssetFreezeSchema(BaseModel):
    """Fields for an asset freeze transaction.

    Definition:
    data/transactions/asset.go : AssetFreezeTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    asset_id: int = Field(alias="asset-id")
    new_freeze_status: bool = Field(alias="new-freeze-status")
