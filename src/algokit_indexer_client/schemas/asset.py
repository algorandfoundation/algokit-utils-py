from pydantic import BaseModel, ConfigDict, Field


class AssetSchema(BaseModel):
    """Specifies both the unique identifier and the parameters for an asset"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    index: int = Field(default=None, alias="index")
    deleted: bool | None = Field(default=None, alias="deleted")
    created_at_round: int | None = Field(default=None, alias="created-at-round")
    destroyed_at_round: int | None = Field(default=None, alias="destroyed-at-round")
    params: "AssetParamsSchema" = Field(default=None, alias="params")
