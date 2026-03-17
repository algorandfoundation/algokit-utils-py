from pydantic import BaseModel, ConfigDict, Field


class TransactionAssetConfigSchema(BaseModel):
    """Fields for asset allocation, re-configuration, and destruction.


    A zero value for asset-id indicates asset creation.
    A zero value for the params indicates asset destruction.

    Definition:
    data/transactions/asset.go : AssetConfigTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    asset_id: int | None = Field(default=None, alias="asset-id")
    params: "AssetParamsSchema | None" = Field(default=None, alias="params")
