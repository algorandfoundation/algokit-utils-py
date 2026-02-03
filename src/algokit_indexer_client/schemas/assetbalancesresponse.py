from pydantic import BaseModel, ConfigDict, Field


class AssetBalancesResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    balances: "list[MiniAssetHoldingSchema]" = Field(default=None, alias="balances")
    current_round: int = Field(default=None, alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
