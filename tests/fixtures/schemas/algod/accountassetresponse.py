from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AccountAssetResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round: int = Field(default=None, alias="round")
    asset_holding: "AssetHoldingSchema | None" = Field(default=None, alias="asset-holding")
    created_asset: "AssetParamsSchema | None" = Field(default=None, alias="created-asset")
