from pydantic import BaseModel, ConfigDict, Field


class AccountAssetsInformationResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round: int = Field(default=None, alias="round")
    next_token: str | None = Field(default=None, alias="next-token")
    asset_holdings: "list[AccountAssetHoldingSchema] | None" = Field(default=None, alias="asset-holdings")
