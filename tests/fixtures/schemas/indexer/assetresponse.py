from pydantic import BaseModel, ConfigDict, Field


class AssetResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    asset: "AssetSchema" = Field(alias="asset")
    current_round: int = Field(alias="current-round")
