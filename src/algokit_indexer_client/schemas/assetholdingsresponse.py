from pydantic import BaseModel, ConfigDict, Field


class AssetHoldingsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    current_round: int = Field(default=None, alias="current-round")
    next_token: str | None = Field(default=None, alias="next-token")
    assets: "list[AssetHoldingSchema]" = Field(default=None, alias="assets")
