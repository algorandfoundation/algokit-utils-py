from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AccountAssetHoldingSchema(BaseModel):
    """AccountAssetHolding describes the account's asset holding and asset parameters (if either exist) for a specific asset ID."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    asset_holding: "AssetHoldingSchema" = Field(default=None, alias="asset-holding")
    asset_params: "AssetParamsSchema | None" = Field(default=None, alias="asset-params")
